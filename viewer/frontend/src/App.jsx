import { useState, useEffect, useMemo } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

function App() {
  const [payload, setPayload] = useState(null);
  const [summary, setSummary] = useState(null);
  const [summaryOpen, setSummaryOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedCovenant, setSelectedCovenant] = useState(null);
  const [selectedTerm, setSelectedTerm] = useState('');
  const [numPages, setNumPages] = useState(null);

  const [reviews, setReviews] = useState([]);
  const [reviewMode, setReviewMode] = useState('idle');
  const [corrections, setCorrections] = useState([]);
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState(null);

  useEffect(() => {
    Promise.all([
      fetch('/api/document-data').then((res) => {
        if (!res.ok) throw new Error('Failed to fetch pipeline data');
        return res.json();
      }),
      fetch('/api/pipeline-summary').then((res) => {
        if (!res.ok) throw new Error('Failed to fetch pipeline summary');
        return res.json();
      }),
      fetch('/api/review').then((res) => {
        if (!res.ok) throw new Error('Failed to fetch review ledger');
        return res.json();
      }),
    ])
      .then(([data, summaryData, reviewData]) => {
        setPayload(data);
        setSummary(summaryData);
        setReviews(reviewData);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const uniqueCovenants = useMemo(() => {
    if (!payload?.Phase1_Extracted_Covenants) return [];
    const seen = new Set();
    return payload.Phase1_Extracted_Covenants.filter((cov) => {
      if (!cov.Agent) return false;
      const isDuplicate = seen.has(cov.Agent);
      seen.add(cov.Agent);
      return !isDuplicate;
    });
  }, [payload]);

  const pagesToRender = useMemo(() => {
    if (!selectedCovenant?.Receipt) return [1];
    const match = selectedCovenant.Receipt.match(/PDF Pages? (\d+)(?:-(\d+))?/);
    if (!match) return [1];

    const start = parseInt(match[1], 10);
    const end = match[2] ? parseInt(match[2], 10) : start;

    const range = [];
    for (let i = start; i <= end; i++) range.push(i);
    return range;
  }, [selectedCovenant]);

  const availableTerms = useMemo(() => {
    if (!selectedCovenant || !payload?.Phase2_Master_Glossary) return [];

    const jsonString = JSON.stringify(selectedCovenant.Extracted_Data);
    const regex = /\[\$REF:\s*(.*?)\]/g;
    const foundTerms = new Set();

    let match;
    while ((match = regex.exec(jsonString)) !== null) {
      foundTerms.add(match[1]);
    }

    const expandedTerms = new Set(foundTerms);
    foundTerms.forEach((term) => {
      const def = payload.Phase2_Master_Glossary[term];
      if (def?.nested_references) {
        def.nested_references.forEach((nested) => expandedTerms.add(nested));
      }
    });

    return Array.from(expandedTerms).sort();
  }, [selectedCovenant, payload]);

  useEffect(() => {
    setSelectedTerm(availableTerms.length > 0 ? availableTerms[0] : '');
  }, [availableTerms]);

  useEffect(() => {
    setReviewMode('idle');
    setCorrections([]);
    setPostError(null);
  }, [selectedCovenant]);

  const skipFieldKeys = ['is_false_flag', 'false_flag_reason', 'is_applicable', 'confidence_score'];

  const stringifyValue = (value) => {
    if (value === null || value === undefined) return '';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const flattenExtractedData = (data, prefix = '') => {
    if (typeof data !== 'object' || data === null) {
      return prefix ? [prefix] : [];
    }

    if (Array.isArray(data)) {
      return data.flatMap((item, index) => {
        const path = prefix ? `${prefix}.${index}` : String(index);
        if (typeof item === 'object' && item !== null) {
          return flattenExtractedData(item, path);
        }
        return [path];
      });
    }

    return Object.entries(data).flatMap(([key, value]) => {
      if (skipFieldKeys.includes(key.toLowerCase())) return [];
      const path = prefix ? `${prefix}.${key}` : key;
      if (typeof value === 'object' && value !== null) {
        return flattenExtractedData(value, path);
      }
      return [path];
    });
  };

  const getValueAtPath = (data, path) => {
    if (!path) return undefined;
    return path.split('.').reduce((current, segment) => {
      if (current === null || current === undefined) return undefined;
      if (Array.isArray(current)) {
        const index = Number(segment);
        return Number.isNaN(index) ? undefined : current[index];
      }
      return current[segment];
    }, data);
  };

  const isReviewed = (cov, reviewRows) =>
    reviewRows.some(
      (row) => row.covenant_agent === cov.Agent && row.receipt === cov.Receipt,
    );

  const fieldPaths = useMemo(() => {
    if (!selectedCovenant?.Extracted_Data) return [];
    return flattenExtractedData(selectedCovenant.Extracted_Data).sort();
  }, [selectedCovenant]);

  const selectedCovenantReviewed = selectedCovenant ? isReviewed(selectedCovenant, reviews) : false;

  const refreshReviews = () =>
    fetch('/api/review')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to refresh review ledger');
        return res.json();
      })
      .then((reviewData) => setReviews(reviewData));

  const submitReview = async (verdict, correctionRows = []) => {
    if (!selectedCovenant || posting) return;

    setPosting(true);
    setPostError(null);

    try {
      const response = await fetch('/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          covenant_agent: selectedCovenant.Agent,
          receipt: selectedCovenant.Receipt,
          verdict,
          corrections: correctionRows,
        }),
      });

      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error(errBody.detail || 'Failed to submit review');
      }

      await refreshReviews();
      setReviewMode('idle');
      setCorrections([]);
    } catch (err) {
      setPostError(err.message);
    } finally {
      setPosting(false);
    }
  };

  const startCorrecting = () => {
    setReviewMode('correcting');
    setCorrections([
      {
        field_path: fieldPaths[0] || '',
        ai_value: stringifyValue(getValueAtPath(selectedCovenant?.Extracted_Data, fieldPaths[0])),
        corrected_value: '',
        diagnostic_layer: 'unknown',
        analyst_note: '',
      },
    ]);
    setPostError(null);
  };

  const updateCorrection = (index, field, value) => {
    setCorrections((prev) =>
      prev.map((row, i) => {
        if (i !== index) return row;
        const updated = { ...row, [field]: value };
        if (field === 'field_path') {
          updated.ai_value = stringifyValue(
            getValueAtPath(selectedCovenant?.Extracted_Data, value),
          );
        }
        return updated;
      }),
    );
  };

  const addCorrectionRow = () => {
    const nextPath = fieldPaths.find((path) => !corrections.some((row) => row.field_path === path)) || '';
    setCorrections((prev) => [
      ...prev,
      {
        field_path: nextPath,
        ai_value: stringifyValue(getValueAtPath(selectedCovenant?.Extracted_Data, nextPath)),
        corrected_value: '',
        diagnostic_layer: 'unknown',
        analyst_note: '',
      },
    ]);
  };

  const submitCorrections = () => {
    const payload = corrections
      .filter((row) => row.field_path && row.corrected_value !== '')
      .map((row) => {
        const entry = {
          field_path: row.field_path,
          ai_value: row.ai_value,
          corrected_value: row.corrected_value,
        };
        if (row.diagnostic_layer && row.diagnostic_layer !== 'unknown') {
          entry.diagnostic_layer = row.diagnostic_layer;
        }
        if (row.analyst_note?.trim()) {
          entry.analyst_note = row.analyst_note.trim();
        }
        return entry;
      });

    if (payload.length === 0) {
      setPostError('Add at least one correction with a corrected value.');
      return;
    }

    submitReview('corrected', payload);
  };

  const formatAgentName = (name) => {
    if (!name) return 'Unknown Agent';
    return name.replace(/([A-Z])/g, ' $1').trim();
  };

  const getAuditInfo = (covenant) => {
    const audit = covenant.Validation_Audit ?? {};
    const extracted = covenant.Extracted_Data ?? {};
    return {
      confidence: audit.confidence_score ?? 1,
      isVerified: audit.is_verified ?? true,
      discrepancies: audit.flagged_discrepancies,
      falseFlag: extracted.is_false_flag === true,
      falseFlagReason: extracted.false_flag_reason,
    };
  };

  const renderFormattedData = (data) => {
    if (typeof data !== 'object' || data === null) {
      if (typeof data === 'string' && data.includes('[$REF:')) {
        return <span className="text-blue-400 font-semibold">{data}</span>;
      }
      return <span className="text-slate-200">{String(data)}</span>;
    }

    if (Array.isArray(data)) {
      return (
        <ul className="list-disc pl-5 mt-2 space-y-2">
          {data.map((item, i) => (
            <li key={i}>{renderFormattedData(item)}</li>
          ))}
        </ul>
      );
    }

    return (
      <div className="space-y-3 mt-2">
        {Object.entries(data).map(([key, value]) => {
          const skipKeys = ['is_false_flag', 'false_flag_reason', 'is_applicable', 'confidence_score'];
          if (skipKeys.includes(key.toLowerCase())) return null;

          return (
            <div key={key} className="bg-slate-800/80 p-3 rounded border border-slate-700/50">
              <span className="font-bold text-slate-400 uppercase tracking-wider text-xs">
                {key.replace(/_/g, ' ')}
              </span>
              <div className="mt-1">{renderFormattedData(value)}</div>
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-blue-400 font-bold">
        Initializing Covenant Viewer...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-red-500 font-bold">
        Error: {error}
      </div>
    );
  }

  const selectedAudit = selectedCovenant ? getAuditInfo(selectedCovenant) : null;

  return (
    <div className="flex h-screen w-full bg-slate-900 text-slate-100 overflow-hidden font-sans flex-col">
      {summary && (
        <div className="border-b border-slate-700 bg-slate-800 shrink-0">
          <button
            type="button"
            onClick={() => setSummaryOpen(!summaryOpen)}
            className="w-full flex items-center justify-between px-4 py-2 text-left hover:bg-slate-700/50"
          >
            <span className="text-sm font-bold text-blue-400 tracking-wider">PIPELINE RUN SUMMARY</span>
            <span className="text-xs text-slate-400">{summaryOpen ? 'Hide' : 'Show'}</span>
          </button>
          {summaryOpen && (
            <div className="px-4 pb-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="bg-slate-900/60 p-2 rounded border border-slate-700">
                <div className="text-slate-500 uppercase">Audit Status</div>
                <div className="font-semibold text-slate-200">
                  {summary.document_metadata?.Audit_Status ?? 'Unknown'}
                </div>
              </div>
              <div className="bg-slate-900/60 p-2 rounded border border-slate-700">
                <div className="text-slate-500 uppercase">Covenants</div>
                <div className="font-semibold text-slate-200">{summary.covenant_count}</div>
              </div>
              <div className="bg-slate-900/60 p-2 rounded border border-slate-700">
                <div className="text-slate-500 uppercase">Validation</div>
                <div className="font-semibold">
                  <span className="text-green-400">{summary.validation_pass} pass</span>
                  {' / '}
                  <span className="text-yellow-400">{summary.validation_fail} fail</span>
                </div>
              </div>
              <div className="bg-slate-900/60 p-2 rounded border border-slate-700">
                <div className="text-slate-500 uppercase">Extraction Cost</div>
                <div className="font-semibold text-slate-200">
                  ${summary.total_extraction_cost_usd?.toFixed(4) ?? '0.0000'}
                </div>
              </div>
              {summary.dispatch_envelope_count != null && (
                <div className="bg-slate-900/60 p-2 rounded border border-slate-700 col-span-2">
                  <div className="text-slate-500 uppercase">Dispatch Envelopes</div>
                  <div className="font-semibold text-slate-200">{summary.dispatch_envelope_count}</div>
                </div>
              )}
              {summary.covenants?.some((c) => !c.is_verified) && (
                <div className="bg-slate-900/60 p-2 rounded border border-yellow-700/50 col-span-2 md:col-span-4">
                  <div className="text-yellow-400 font-semibold mb-1">Failed Validation</div>
                  <ul className="text-slate-300 space-y-1">
                    {summary.covenants
                      .filter((c) => !c.is_verified)
                      .map((c) => (
                        <li key={c.agent}>
                          {formatAgentName(c.agent)} — {(c.confidence_score * 100).toFixed(0)}% confidence
                        </li>
                      ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* COLUMN 1: The Queue */}
        <div className="w-1/4 border-r border-slate-700 bg-slate-800 p-4 flex flex-col">
          <h2 className="text-lg font-bold mb-4 text-blue-400 tracking-wider">PHASE 1 QUEUE</h2>
          <div className="text-sm text-slate-400 mb-4 pb-2 border-b border-slate-700">
            {uniqueCovenants.length} Unique Covenants
          </div>
          <div className="flex-1 overflow-y-auto pr-2 space-y-2">
            {uniqueCovenants.map((cov, index) => {
              const audit = getAuditInfo(cov);
              const reviewed = isReviewed(cov, reviews);
              const receiptParts = cov.Receipt ? cov.Receipt.split('|') : [];
              const pageReceipt = receiptParts[0]?.trim();
              const sectionReceipt = receiptParts.slice(1).join(' | ').trim();

              return (
                <button
                  key={index}
                  type="button"
                  onClick={() => setSelectedCovenant(cov)}
                  className={`w-full text-left p-3 rounded border transition-all duration-200 ${
                    selectedCovenant === cov
                      ? 'bg-blue-900/40 border-blue-500 text-blue-100 shadow-md'
                      : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700 hover:border-slate-500'
                  }`}
                >
                  <div className="font-semibold text-sm flex items-center justify-between gap-2">
                    <span>{formatAgentName(cov.Agent)}</span>
                    <span className="flex gap-1 shrink-0">
                      {reviewed && (
                        <span className="text-purple-300 text-xs bg-purple-900/30 px-2 py-0.5 rounded">
                          Reviewed
                        </span>
                      )}
                      {audit.falseFlag && (
                        <span className="text-red-400 text-xs bg-red-900/30 px-2 py-0.5 rounded">Flagged</span>
                      )}
                      {!audit.isVerified && (
                        <span className="text-yellow-400 text-xs bg-yellow-900/30 px-2 py-0.5 rounded">
                          Audit {(audit.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                      {audit.isVerified && (
                        <span className="text-green-400 text-xs bg-green-900/30 px-2 py-0.5 rounded">Verified</span>
                      )}
                    </span>
                  </div>
                  <div className="text-xs mt-2 text-slate-400 space-y-1">
                    {pageReceipt && <div>{pageReceipt}</div>}
                    {sectionReceipt && <div className="text-slate-500">{sectionReceipt}</div>}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* COLUMN 2: Document Provenance */}
        <div className="w-2/4 flex flex-col p-4 bg-slate-900 relative">
          <h2 className="text-lg font-bold mb-4 text-blue-400 tracking-wider flex justify-between items-center">
            <span>SOURCE DOCUMENT PROVENANCE</span>
            {selectedCovenant && (
              <span className="text-sm text-slate-500 font-normal border border-slate-700 px-2 py-1 rounded bg-slate-800">
                Pages {pagesToRender[0]}{' '}
                {pagesToRender.length > 1 ? `- ${pagesToRender[pagesToRender.length - 1]}` : ''} of{' '}
                {numPages || '?'}
              </span>
            )}
          </h2>
          <div className="flex-1 border border-slate-700 rounded bg-slate-800/30 overflow-y-auto flex flex-col items-center p-4 space-y-6">
            <Document
              file="/api/pdf"
              onLoadSuccess={({ numPages: total }) => setNumPages(total)}
              loading={
                <span className="text-slate-500 font-medium animate-pulse">Rendering Document Spread...</span>
              }
            >
              {pagesToRender.map((pageNum) => (
                <div
                  key={pageNum}
                  className="mb-6 shadow-2xl drop-shadow-2xl rounded overflow-hidden border border-slate-700"
                >
                  <Page
                    pageNumber={pageNum}
                    width={700}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                  />
                </div>
              ))}
            </Document>
          </div>
        </div>

        {/* COLUMN 3: Audit & Glossary */}
        <div className="w-1/4 border-l border-slate-700 bg-slate-800 flex flex-col">
          <div className="p-4 h-3/5 border-b border-slate-700 flex flex-col">
            <h2 className="text-lg font-bold mb-4 text-blue-400 tracking-wider shrink-0">EXTRACTED MATH</h2>

            <div className="flex-1 overflow-y-auto pr-2">
              {selectedCovenant && selectedAudit ? (
                <>
                  <div className="mb-4 bg-slate-900 border border-slate-700 p-3 rounded flex flex-col gap-2 shadow-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-slate-400 uppercase tracking-wider font-bold">
                        Validation Confidence
                      </span>
                      <span
                        className={`text-sm font-bold ${
                          selectedAudit.confidence < 1 ? 'text-yellow-400' : 'text-green-400'
                        }`}
                      >
                        {(selectedAudit.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">
                      Verified: {selectedAudit.isVerified ? 'Yes' : 'No'}
                    </div>

                    {selectedAudit.falseFlag && selectedAudit.falseFlagReason && (
                      <div className="text-xs text-red-400 border-t border-slate-700 pt-2 mt-1">
                        <span className="font-bold">False Flag: </span>
                        {selectedAudit.falseFlagReason}
                      </div>
                    )}

                    {selectedAudit.discrepancies?.length > 0 && (
                      <div className="text-xs text-yellow-400 border-t border-slate-700 pt-2 mt-1 space-y-1">
                        <span className="font-bold">Audit Flags:</span>
                        <ul className="list-disc pl-4">
                          {selectedAudit.discrepancies.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="mb-4 bg-slate-900 border border-slate-700 p-3 rounded flex flex-col gap-3 shadow-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-slate-400 uppercase tracking-wider font-bold">
                        Analyst Review
                      </span>
                      {selectedCovenantReviewed && (
                        <span className="text-purple-300 text-xs bg-purple-900/30 px-2 py-0.5 rounded">
                          Reviewed
                        </span>
                      )}
                    </div>

                    {postError && (
                      <div className="text-xs text-red-400 border border-red-800/50 bg-red-900/20 p-2 rounded">
                        {postError}
                      </div>
                    )}

                    {selectedCovenantReviewed ? (
                      <div className="text-xs text-slate-400 italic">
                        This covenant has a recorded analyst verdict.
                      </div>
                    ) : (
                      <>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            disabled={posting}
                            onClick={() => submitReview('approved')}
                            className="flex-1 text-xs font-semibold px-3 py-2 rounded border border-green-600 bg-green-900/30 text-green-300 hover:bg-green-900/50 disabled:opacity-50"
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            disabled={posting}
                            onClick={() =>
                              reviewMode === 'correcting' ? setReviewMode('idle') : startCorrecting()
                            }
                            className="flex-1 text-xs font-semibold px-3 py-2 rounded border border-yellow-600 bg-yellow-900/30 text-yellow-300 hover:bg-yellow-900/50 disabled:opacity-50"
                          >
                            {reviewMode === 'correcting' ? 'Cancel' : 'Correct'}
                          </button>
                        </div>

                        {reviewMode === 'correcting' && (
                          <div className="space-y-3 border-t border-slate-700 pt-3">
                            {corrections.map((row, index) => (
                              <div
                                key={index}
                                className="space-y-2 border border-slate-700/70 rounded p-2 bg-slate-800/40"
                              >
                                <select
                                  className="w-full bg-slate-900 border border-slate-600 text-slate-200 text-xs rounded p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                                  value={row.field_path}
                                  onChange={(e) => updateCorrection(index, 'field_path', e.target.value)}
                                >
                                  {fieldPaths.map((path) => (
                                    <option key={path} value={path}>
                                      {path}
                                    </option>
                                  ))}
                                </select>

                                <div className="text-xs text-slate-500">
                                  AI value: <span className="text-slate-300">{row.ai_value || '—'}</span>
                                </div>

                                <input
                                  type="text"
                                  placeholder="Corrected value"
                                  value={row.corrected_value}
                                  onChange={(e) => updateCorrection(index, 'corrected_value', e.target.value)}
                                  className="w-full bg-slate-900 border border-slate-600 text-slate-200 text-xs rounded p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                                />

                                <select
                                  className="w-full bg-slate-900 border border-slate-600 text-slate-200 text-xs rounded p-2 focus:ring-1 focus:ring-blue-500 outline-none"
                                  value={row.diagnostic_layer}
                                  onChange={(e) => updateCorrection(index, 'diagnostic_layer', e.target.value)}
                                >
                                  <option value="unknown">unknown</option>
                                  <option value="L0">L0</option>
                                  <option value="L1">L1</option>
                                  <option value="L2">L2</option>
                                  <option value="L3">L3</option>
                                </select>

                                <textarea
                                  placeholder="Analyst note (optional)"
                                  value={row.analyst_note}
                                  onChange={(e) => updateCorrection(index, 'analyst_note', e.target.value)}
                                  className="w-full bg-slate-900 border border-slate-600 text-slate-200 text-xs rounded p-2 min-h-[4rem] resize-y focus:ring-1 focus:ring-blue-500 outline-none"
                                />
                              </div>
                            ))}

                            <div className="flex gap-2">
                              <button
                                type="button"
                                disabled={posting}
                                onClick={addCorrectionRow}
                                className="text-xs px-3 py-2 rounded border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-50"
                              >
                                + Add another
                              </button>
                              <button
                                type="button"
                                disabled={posting}
                                onClick={submitCorrections}
                                className="flex-1 text-xs font-semibold px-3 py-2 rounded border border-blue-500 bg-blue-900/40 text-blue-200 hover:bg-blue-900/60 disabled:opacity-50"
                              >
                                Submit corrections
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>

                  {renderFormattedData(selectedCovenant.Extracted_Data)}
                </>
              ) : (
                <div className="text-sm text-slate-400 italic">Select an item from the queue to view data.</div>
              )}
            </div>
          </div>

          <div className="p-4 flex-1 flex flex-col overflow-hidden">
            <h2 className="text-lg font-bold mb-4 text-blue-400 tracking-wider shrink-0">DYNAMIC GLOSSARY</h2>

            {!selectedCovenant ? (
              <div className="text-sm text-slate-400 italic">Select an item from the queue.</div>
            ) : availableTerms.length === 0 ? (
              <div className="text-sm text-slate-500">No legal terms detected in this covenant.</div>
            ) : (
              <div className="flex flex-col h-full">
                <select
                  className="w-full bg-slate-900 border border-slate-600 text-slate-200 text-sm rounded p-2 mb-4 focus:ring-1 focus:ring-blue-500 outline-none"
                  value={selectedTerm}
                  onChange={(e) => setSelectedTerm(e.target.value)}
                >
                  {availableTerms.map((term) => (
                    <option key={term} value={term}>
                      {term}
                    </option>
                  ))}
                </select>

                <div className="flex-1 overflow-y-auto bg-slate-900/50 p-3 rounded border border-slate-700/50">
                  {selectedTerm && payload?.Phase2_Master_Glossary[selectedTerm] ? (
                    <p className="text-sm text-slate-300 leading-relaxed">
                      {payload.Phase2_Master_Glossary[selectedTerm].raw_definition_text}
                    </p>
                  ) : (
                    <span className="text-red-400 text-sm">Definition not found in Phase 2 payload.</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
