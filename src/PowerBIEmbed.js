import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './PowerBIEmbed.css';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { saveAs } from 'file-saver';

const PowerBIEmbed = ({ role, username }) => {
  const reportRef = useRef(null);
  const [reports, setReports] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [reportPages, setReportPages] = useState([]);
  const [activePage, setActivePage] = useState(null);
  const [selectedPage, setSelectedPage] = useState(null);
  const [visuals, setVisuals] = useState([]);
  const [selectedVisual, setSelectedVisual] = useState(null);
  const [exportFormat, setExportFormat] = useState('xlsx');
  const navigate = useNavigate();

  const fetchReports = async () => {
    try {
      const res = await fetch(`https://dev-oneoliva.olivaclinic.com/backend/get-reports?username=${username}`);
      if (!res.ok) throw new Error('Failed to fetch report list');
      const data = await res.json();
      setReports(data);
      if (data.length > 0) setActiveReport(data[0]);
    } catch (err) {
      console.error('Failed to fetch reports:', err);
      toast.error("❌ Could not load reports");
    }
  };

  const fetchUserFilters = async (report) => {
    try {
      const res = await fetch(`https://dev-oneoliva.olivaclinic.com/backend/get-user-filters/${username}/${report.report_id}`);
      if (!res.ok) throw new Error('Failed to fetch user filters');
      const data = await res.json();
      return data.filters;
    } catch (err) {
      console.error('Failed to fetch user filters:', err);
      return [];
    }
  };

  const applyUserFilters = async (embeddedReport, filters) => {
    try {
      // Get models from window.powerbi
      const models = window['powerbi-client'].models;
      if (!models) {
        throw new Error('Power BI models not available');
      }

      const powerbiFilters = filters.map(filter => ({
        $schema: "http://powerbi.com/product/schema#basic",
        target: {
          table: filter.table_name,
          column: filter.column_name
        },
        operator: filter.operator,
        values: filter.filter_values,
        filterType: models.FilterType.Basic,
        requireSingleSelection: false
      }));

      if (powerbiFilters.length > 0) {
        await embeddedReport.setFilters(powerbiFilters);
        console.log('✅ User filters applied:', powerbiFilters);
      }
    } catch (err) {
      console.error('Failed to apply user filters:', err);
      toast.error("❌ Failed to apply filters");
    }
  };

  const handlePageChange = async (page) => {
    try {
      await page.setActive();
      setActivePage(page.name);
      console.log(`Navigated to page: ${page.name}`);
    } catch (err) {
      console.error('Failed to change page:', err);
      toast.error("❌ Failed to change page");
    }
  };

  const embedReport = async (report) => {
    try {
      const res = await fetch('https://dev-oneoliva.olivaclinic.com/backend/get-powerbi-tokens', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          group_id: report.group_id,
          report_id: report.report_id,
          username: username
        }),
      });

      if (!res.ok) throw new Error('Failed to fetch Power BI token');
      const data = await res.json();
      const accessToken = data.access_token || data.accessToken;

      // Ensure Power BI client is loaded
      if (!window.powerbi) {
        throw new Error('Power BI client SDK not loaded');
      }

      const models = window['powerbi-client'].models;
      if (!models) {
        throw new Error('Power BI models not available');
      }

      const embedConfig = {
        type: 'report',
        id: report.report_id,
        embedUrl: `https://app.powerbi.com/reportEmbed?reportId=${report.report_id}&groupId=${report.group_id}`,
        accessToken,
        tokenType: models.TokenType.Embed,
        settings: {
          panes: {
            filters: { visible: false },
            pageNavigation: { visible: false }  // Hide default page navigation
          },
          bars: {
            actionBar: { visible: false }
          },
          // Add visual settings to hide headers for unauthorized pages
          visualSettings: {
            visualHeaders: [
              {
                settings: {
                  visible: false
                }
              }
            ]
          }
        },
        permissions: models.Permissions.Read,
        viewMode: models.ViewMode.View
      };

      if (window.powerbi && reportRef.current) {
        window.powerbi.reset(reportRef.current);
        const embeddedReport = window.powerbi.embed(reportRef.current, embedConfig);

        embeddedReport.on('loaded', async () => {
          console.log('✅ Report loaded');

          try {
            // Get all pages
            const pages = await embeddedReport.getPages();
            console.log('Available page IDs:', pages.map(p => p.name));
            
            // Filter allowed pages based on role and report configuration
            let allowedPages = pages;
            if (role !== 'admin' && report.allowed_pages) {
              allowedPages = pages.filter(p => report.allowed_pages.includes(p.name));
              console.log('Filtered to allowed pages:', allowedPages.map(p => p.name));
              
              // For non-admin users, hide unauthorized pages
              const unauthorizedPages = pages.filter(p => !report.allowed_pages.includes(p.name));
              for (const page of unauthorizedPages) {
                try {
                  // Set visibility to hidden for unauthorized pages
                  await page.setVisibility(1); // 1 = Hidden in View Mode
                } catch (err) {
                  console.error('Failed to hide page:', page.name, err);
                }
              }
            }

            // Store pages for navigation
            setReportPages(allowedPages);

            // Navigate to first allowed page
            if (allowedPages.length > 0) {
              await handlePageChange(allowedPages[0]);
            }

            // Fetch and apply user-specific filters
            const userFilters = await fetchUserFilters(report);
            await applyUserFilters(embeddedReport, userFilters);

          } catch (err) {
            console.error('❌ Failed during report post-load handling:', err);
            toast.error("❌ Could not finalize report setup");
          }
        });

        embeddedReport.on('error', (event) => {
          console.error('❌ Power BI error:', event.detail);
          toast.error("❌ Power BI Error");
        });
      }
    } catch (err) {
      console.error('Embedding failed:', err);
      toast.error("❌ Embedding failed");
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    toast.success("✅ Logged out successfully");
    setTimeout(() => {
      navigate('/powerbi');
      window.location.reload();
    }, 1000);
  };

  const handleExport = async () => {
    if (!activeReport) {
      toast.error('No report selected');
      return;
    }
    try {
      const res = await fetch('https://dev-oneoliva.olivaclinic.com/backend/export-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username,
          report_id: activeReport.report_id,
          file_type: 'csv',
        }),
      });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      saveAs(blob, `report_${activeReport.report_id}.csv`);
      toast.success('✅ Exported report!');
    } catch (err) {
      console.error('Export failed:', err);
      toast.error('❌ Export failed');
    }
  };

  const fetchVisuals = async (page) => {
    if (!page) return;
    try {
      const visuals = await page.getVisuals();
      setVisuals(visuals);
      setSelectedVisual(visuals[0]?.name || null);
    } catch (err) {
      console.error('Failed to fetch visuals:', err);
      setVisuals([]);
      setSelectedVisual(null);
    }
  };

  useEffect(() => {
    if (reportPages.length > 0 && activePage) {
      const pageObj = reportPages.find(p => p.name === activePage);
      setSelectedPage(pageObj);
      fetchVisuals(pageObj);
    }
  }, [activePage, reportPages]);

  useEffect(() => {
    if (activeReport) {
      embedReport(activeReport);
      setReportPages([]); // Reset pages when report changes
      setActivePage(null);
    }
  }, [activeReport]);

  const handleExportVisual = async () => {
    if (!activeReport || !selectedPage || !selectedVisual) {
      toast.error('Select report, page, and visual');
      return;
    }
    try {
      const res = await fetch('https://dev-oneoliva.olivaclinic.com/backend/export-visual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          group_id: activeReport.group_id,
          report_id: activeReport.report_id,
          page_name: selectedPage.name,
          visual_name: selectedVisual,
          format: exportFormat,
          username: username,
        }),
      });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      saveAs(blob, `visual_export.${exportFormat}`);
      toast.success('✅ Visual exported!');
    } catch (err) {
      console.error('Export visual failed:', err);
      toast.error('❌ Export visual failed');
    }
  };

  return (
    <div className="powerbi-container">
      <div className={`sidebar ${isSidebarOpen ? '' : 'auto-hide'}`}>
        <div className="sidebar-header">
          <button className="toggle-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
            {isSidebarOpen ? '⏪' : '⏩'}
          </button>
          {isSidebarOpen && (
            <span className="username">
              👤 {username} ({role})
            </span>
          )}
        </div>

        {isSidebarOpen && (
          <>
            <h3 className="sidebar-title">Available Reports</h3>
            <div className="reports-section">
              {reports.map((r, i) => (
                <button
                  key={i}
                  className={`sidebar-btn ${activeReport?.report_id === r.report_id ? 'active' : ''}`}
                  onClick={() => setActiveReport(r)}
                  title={r.dashboard}
                >
                  <i className="fa fa-chart-bar"></i>
                  {r.dashboard}
                </button>
              ))}
            </div>

            {reportPages.length > 0 && (
              <>
                <h3 className="sidebar-title">Report Pages</h3>
                <div className="pages-section">
                  {reportPages.map((page, i) => (
                    <button
                      key={i}
                      className={`sidebar-btn ${activePage === page.name ? 'active' : ''}`}
                      onClick={() => handlePageChange(page)}
                      title={page.displayName}
                    >
                      <i className="fa fa-file"></i>
                      {page.displayName || page.name}
                    </button>
                  ))}
                </div>
              </>
            )}
          </>
        )}

        <div className="sidebar-footer">
          <button className="sidebar-btn logout-btn" onClick={handleLogout}>
            <i className="fa fa-sign-out-alt"></i>
            {isSidebarOpen ? 'Logout' : '⎋'}
          </button>
        </div>
      </div>

      <div className="report-area">
        <h2 className="report-title">
          {activeReport?.dashboard || 'Select a Report'}
          {activePage && ` - ${activePage}`}
          {activeReport && (
            <button className="export-btn" onClick={handleExport} style={{marginLeft: 16}}>
              Export CSV
            </button>
          )}
        </h2>
        {activeReport && reportPages.length > 0 && (
          <div style={{marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center'}}>
            <label>Page:
              <select value={selectedPage?.name || ''} onChange={e => {
                const page = reportPages.find(p => p.name === e.target.value);
                setSelectedPage(page);
                fetchVisuals(page);
              }}>
                {reportPages.map(page => (
                  <option key={page.name} value={page.name}>{page.displayName || page.name}</option>
                ))}
              </select>
            </label>
            <label>Visual:
              <select value={selectedVisual || ''} onChange={e => setSelectedVisual(e.target.value)}>
                {visuals.map(v => (
                  <option key={v.name} value={v.name}>{v.title || v.name}</option>
                ))}
              </select>
            </label>
            <label>Format:
              <select value={exportFormat} onChange={e => setExportFormat(e.target.value)}>
                <option value="xlsx">Excel (xlsx)</option>
                <option value="csv">CSV</option>
              </select>
            </label>
            <button className="export-btn" onClick={handleExportVisual}>
              Export Visual
            </button>
          </div>
        )}
        <div ref={reportRef} className="report-frame" />
      </div>
    </div>
  );
};

export default PowerBIEmbed;
