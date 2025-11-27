import React from 'react';
import clsx from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'danger';
    size?: 'sm' | 'md' | 'lg';
}

export default function Button({
    children,
    className,
    variant = 'primary',
    size = 'md',
    ...props
}: ButtonProps) {
    return (
        <button
            className={clsx(
                'rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900',
                {
                    'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500': variant === 'primary',
                    'bg-gray-700 text-white hover:bg-gray-600 focus:ring-gray-500': variant === 'secondary',
                    'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500': variant === 'danger',
                    'px-3 py-1.5 text-sm': size === 'sm',
                    'px-4 py-2 text-base': size === 'md',
                    'px-6 py-3 text-lg': size === 'lg',
                    'opacity-50 cursor-not-allowed': props.disabled,
                },
                className
            )}
            {...props}
        >
            {children}
        </button>
    );
}
