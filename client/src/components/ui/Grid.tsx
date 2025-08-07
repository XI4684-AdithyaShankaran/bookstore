"use client";

import React, { ReactNode, useMemo } from 'react';

interface GridProps {
    children: ReactNode;
    columns?: {
        sm?: number;
        md?: number;
        lg?: number;
        xl?: number;
        '2xl'?: number;
    };
    gap?: number;
    className?: string;
}

export default function Grid({
    children,
    columns = { sm: 1, md: 2, lg: 3, xl: 4, '2xl': 5 },
    gap = 4,
    className = ""
}: GridProps) {
    // Generate responsive column classes
    const columnClasses = useMemo(() => {
        const classes = [];
        
        if (columns.sm) classes.push(`sm:columns-${columns.sm}`);
        if (columns.md) classes.push(`md:columns-${columns.md}`);
        if (columns.lg) classes.push(`lg:columns-${columns.lg}`);
        if (columns.xl) classes.push(`xl:columns-${columns.xl}`);
        if (columns['2xl']) classes.push(`2xl:columns-${columns['2xl']}`);
        
        // Default single column
        classes.unshift('columns-1');
        
        return classes.join(' ');
    }, [columns]);

    return (
        <div 
            className={`
                ${columnClasses} 
                gap-${gap} 
                space-y-${gap} 
                ${className}
            `.trim()}
        >
            {children}
        </div>
    );
} 