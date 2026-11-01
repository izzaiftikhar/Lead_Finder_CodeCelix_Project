# Removes files from earlier prototypes that v2 does not use. Run from the repo root, review with `git status`.
$paths = @(
 "app_backup","static","components","index.html","vite.config.js","eslint.config.js",
 "EvidencePanel.tsx","ExportControls.tsx","LeadDetailsExample.tsx","api.ts","types.ts","exportCsv.ts","mockEvidence.ts",
 "src/App.jsx","src/main.jsx","src/index.css","src/pages","src/layouts","src/services","src/config","src/data",
 "src/components/FilterBar.tsx","src/components/ResultsTable.tsx","src/components/ResultsTable.jsx","src/components/SearchFilters.jsx",
 "src/components/SearchForm.tsx","src/components/StatusBadge.tsx","src/components/FindLeads.tsx","src/components/LeadDrawer.tsx","src/components/LeadList.tsx",
 "src/lib/csv.ts"
)
foreach ($p in $paths) { if (Test-Path $p) { git rm -r -q --cached --ignore-unmatch $p; Remove-Item -Recurse -Force $p } }
Write-Host "Done. Remaining src/components:"; Get-ChildItem src\components -Name
