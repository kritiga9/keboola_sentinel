import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar.jsx'
import ROIAnalysis from './pages/ROIAnalysis.jsx'
import AssetInventory from './pages/AssetInventory.jsx'
import ImpactAnalysis from './pages/ImpactAnalysis.jsx'
import { fetchOrganizations } from './api/client.js'

export default function App() {
  const [page, setPage] = useState('roi')
  const [selectedOrg, setSelectedOrg] = useState('All Organizations')
  const [orgs, setOrgs] = useState([])

  useEffect(() => {
    fetchOrganizations()
      .then(setOrgs)
      .catch(console.error)
  }, [])

  const pages = {
    roi:       <ROIAnalysis selectedOrg={selectedOrg} />,
    inventory: <AssetInventory selectedOrg={selectedOrg} />,
    impact:    <ImpactAnalysis selectedOrg={selectedOrg} />,
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar
        page={page}
        setPage={setPage}
        selectedOrg={selectedOrg}
        setSelectedOrg={setSelectedOrg}
        orgs={orgs}
      />
      {/* Main content offset for fixed sidebar */}
      <main className="ml-64 flex-1 min-w-0">
        <div className="max-w-7xl mx-auto px-8 py-8">
          {pages[page]}
        </div>
      </main>
    </div>
  )
}
