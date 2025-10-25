import React from 'react';
import './Header.css';

interface HeaderProps {
  message: string;
  loading: boolean;
}

const Header: React.FC<HeaderProps> = ({ message, loading }) => {
  return (
    <header className="header">
      <div className="header-content">
        <h1 className="app-title">FocusMind</h1>
        <div className="motivation-message">
          {loading ? (
            <div className="loading-spinner">Loading...</div>
          ) : (
            <p className="message-text">{message}</p>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
