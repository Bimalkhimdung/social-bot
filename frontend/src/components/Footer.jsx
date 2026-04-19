export default function Footer() {
  const currentYear = new Date().getFullYear()
  
  return (
    <footer className="app-footer">
      <div>
        <div className="footer-logo">NEPSE Bot</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
          © {currentYear} Quantum Automation Systems. All rights reserved.
        </div>
      </div>

      <div className="footer-links">
        <a href="#" className="footer-link">Privacy Policy</a>
        <a href="#" className="footer-link">API Docs</a>
        <a href="#" className="footer-link">System Status</a>
        <a href="#" className="footer-link">Support</a>
      </div>
    </footer>
  )
}
