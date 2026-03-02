/**
 * Button — Componente de botón unificado con variantes 'primary' y 'outline'.
 */
export default function Button({
    children,
    variant = "primary",
    onClick,
    className = "",
    icon: Icon,
    id
}) {
    const isOutline = variant === "outline";

    const baseStyles = {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        padding: '10px 16px',
        borderRadius: '12px',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
    };

    const variantStyles = isOutline
        ? {
            border: '1.5px solid #299D91',
            color: '#299D91',
            backgroundColor: 'transparent',
        }
        : {
            backgroundColor: '#299D91',
            color: '#FFFFFF',
            border: '1.5px solid transparent',
        };

    return (
        <button
            id={id}
            onClick={onClick}
            className={`group ${className}`}
            style={{ ...baseStyles, ...variantStyles }}
            onMouseEnter={e => {
                if (isOutline) {
                    e.currentTarget.style.backgroundColor = '#299D9110';
                } else {
                    e.currentTarget.style.backgroundColor = '#22857a';
                }
            }}
            onMouseLeave={e => {
                if (isOutline) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                } else {
                    e.currentTarget.style.backgroundColor = '#299D91';
                }
            }}
        >
            {children}
            {Icon && <span className="shrink-0">{Icon}</span>}
        </button>
    );
}
