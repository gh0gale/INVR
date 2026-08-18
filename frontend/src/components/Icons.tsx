/**
 * Icon set drawn for this product.
 *
 * Deliberately not Lucide: a 16-unit grid, 1.25 stroke, square caps and miter
 * joins, so the marks read as draughting notation next to the ledger type
 * rather than as the rounded 24/2 house style every AI-built site ships with.
 */
import React from 'react';

type IconProps = {
  className?: string;
  title?: string;
};

const Frame: React.FC<React.PropsWithChildren<IconProps>> = ({
  className = 'w-4 h-4',
  title,
  children,
}) => (
  <svg
    viewBox="0 0 16 16"
    className={className}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.25}
    strokeLinecap="square"
    strokeLinejoin="miter"
    aria-hidden={title ? undefined : true}
    role={title ? 'img' : undefined}
  >
    {title ? <title>{title}</title> : null}
    {children}
  </svg>
);

export const IconSearch: React.FC<IconProps> = (p) => (
  <Frame {...p}>
    <circle cx="6.75" cy="6.75" r="4.25" />
    <path d="M10 10 L14 14" />
  </Frame>
);

export const IconPlus: React.FC<IconProps> = (p) => (
  <Frame {...p}>
    <path d="M8 2.5 V13.5 M2.5 8 H13.5" />
  </Frame>
);

export const IconClose: React.FC<IconProps> = (p) => (
  <Frame {...p}>
    <path d="M3.5 3.5 L12.5 12.5 M12.5 3.5 L3.5 12.5" />
  </Frame>
);

export const IconTrash: React.FC<IconProps> = (p) => (
  <Frame {...p}>
    <path d="M2.5 4.5 H13.5" />
    <path d="M5.75 4.5 V2.5 H10.25 V4.5" />
    <path d="M4 4.5 V13.5 H12 V4.5" />
  </Frame>
);

export const IconMarked: React.FC<IconProps> = (p) => (
  <Frame {...p}>
    <path d="M4 2.5 H12 V13.5 L8 10.5 L4 13.5 Z" fill="currentColor" stroke="none" />
  </Frame>
);

/** Panel toggle. A pane with a divider, not a hamburger. */
export const IconPanel: React.FC<IconProps> = (p) => (
  <Frame {...p}>
    <rect x="2.5" y="2.5" width="11" height="11" />
    <path d="M6.5 2.5 V13.5" />
  </Frame>
);

export const IconArrowRight: React.FC<IconProps> = (p) => (
  <Frame {...p}>
    <path d="M2.5 8 H13" />
    <path d="M9 4 L13 8 L9 12" />
  </Frame>
);

export const IconArrowLeft: React.FC<IconProps> = (p) => (
  <Frame {...p}>
    <path d="M13.5 8 H3" />
    <path d="M7 4 L3 8 L7 12" />
  </Frame>
);

/** Caution mark for risk copy. A bounded exclamation, no triangle cliché. */
export const IconCaution: React.FC<IconProps> = (p) => (
  <Frame {...p}>
    <rect x="2.5" y="2.5" width="11" height="11" />
    <path d="M8 5 V8.75" />
    <path d="M8 10.75 V11" />
  </Frame>
);

/** Solid direction markers for signed figures. Never animated. */
export const IconUp: React.FC<IconProps> = ({ className = 'w-3 h-3' }) => (
  <svg viewBox="0 0 16 16" className={className} fill="currentColor" aria-hidden="true">
    <path d="M8 3.5 L13.5 12.5 H2.5 Z" />
  </svg>
);

export const IconDown: React.FC<IconProps> = ({ className = 'w-3 h-3' }) => (
  <svg viewBox="0 0 16 16" className={className} fill="currentColor" aria-hidden="true">
    <path d="M8 12.5 L2.5 3.5 H13.5 Z" />
  </svg>
);
