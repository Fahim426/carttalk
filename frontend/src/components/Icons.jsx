import React from 'react';

export const SpeakIcon = () => (
    <svg width="64" height="64" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="48" height="48" rx="16" fill="var(--secondary-bg)" />
        <path d="M24 13C21.7909 13 20 14.7909 20 17V23C20 25.2091 21.7909 27 24 27C26.2091 27 28 25.2091 28 23V17C28 14.7909 26.2091 13 24 13Z" fill="url(#paint_speak)"/>
        <path d="M16 23V24C16 28.4183 19.5817 32 24 32C28.4183 32 32 28.4183 32 24V23" stroke="url(#paint_speak)" strokeWidth="3" strokeLinecap="round"/>
        <path d="M24 32V37M20 37H28" stroke="url(#paint_speak)" strokeWidth="3" strokeLinecap="round"/>
        <defs>
            <linearGradient id="paint_speak" x1="16" y1="13" x2="32" y2="37" gradientUnits="userSpaceOnUse">
                <stop stopColor="var(--primary-color)"/>
                <stop offset="1" stopColor="#F97316"/>
            </linearGradient>
        </defs>
    </svg>
);

export const SmartCartIcon = () => (
    <svg width="64" height="64" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="48" height="48" rx="16" fill="var(--secondary-bg)" />
        <path d="M13 16H16L18.6 27H31.4L34 16H21" stroke="url(#paint_cart)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
        <circle cx="20" cy="33" r="2.5" fill="url(#paint_cart)"/>
        <circle cx="30" cy="33" r="2.5" fill="url(#paint_cart)"/>
        <path d="M33 14L34 11L37 10L34 9L33 6L32 9L29 10L32 11L33 14Z" fill="var(--accent-color)"/>
        <defs>
            <linearGradient id="paint_cart" x1="13" y1="16" x2="34" y2="33" gradientUnits="userSpaceOnUse">
                <stop stopColor="var(--primary-color)"/>
                <stop offset="1" stopColor="#F97316"/>
            </linearGradient>
        </defs>
    </svg>
);

export const CheckoutIcon = () => (
    <svg width="64" height="64" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="48" height="48" rx="16" fill="var(--secondary-bg)" />
        <circle cx="24" cy="24" r="12" stroke="url(#paint_checkout)" strokeWidth="3"/>
        <path d="M19 24.5L22.5 28L29 20" stroke="url(#paint_checkout)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M33 33L38 38" stroke="var(--accent-color)" strokeWidth="3" strokeLinecap="round"/>
        <path d="M37 33H33V37" stroke="var(--accent-color)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
        <defs>
            <linearGradient id="paint_checkout" x1="12" y1="12" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                <stop stopColor="var(--primary-color)"/>
                <stop offset="1" stopColor="#F97316"/>
            </linearGradient>
        </defs>
    </svg>
);
