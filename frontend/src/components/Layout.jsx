import { Outlet } from 'react-router-dom'
import Header from './Header'
import '../index-modern.css'

export default function Layout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
