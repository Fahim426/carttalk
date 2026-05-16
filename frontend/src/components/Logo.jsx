import React from 'react';

const Logo = ({ size = 36, showText = true, className = "" }) => {
    return (
        <div className={`logo-container ${className}`} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <svg width={size} height={size} viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="36" height="36" rx={size * 0.25} fill="url(#paint0_linear_logo)"/>
                <path d="M11 14C11 12.8954 11.8954 12 13 12H23C24.1046 12 25 12.8954 25 14V22C25 23.1046 24.1046 24 23 24H13C11.8954 24 11 23.1046 11 22V14Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M15 12V10C15 8.34315 16.3431 7 18 7C19.6569 7 21 8.34315 21 10V12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M15 17V19M18 16V20M21 17V19" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <defs>
                    <linearGradient id="paint0_linear_logo" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                        <stop stopColor="#EF6D4A"/>
                        <stop offset="1" stopColor="#F97316"/>
                    </linearGradient>
                </defs>
            </svg>
            {showText && <span style={{ fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-1.5px', fontSize: `${Math.max(20, size * 0.8)}px` }}>CartTalk.</span>}
        </div>
    );
};

export default Logo;
