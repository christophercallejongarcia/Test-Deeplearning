/**
 * Sharing utilities for cloud export feature
 * Generates shareable links, QR codes, and manages access permissions
 */

export type SharePermission = 'view' | 'download' | 'full';
export type ShareExpiration = '24h' | '7d' | '30d' | 'never';

export interface ShareLink {
  id: string;
  url: string;
  permission: SharePermission;
  expiration: ShareExpiration;
  createdAt: Date;
  expiresAt: Date | null;
  password?: string;
  accessCount: number;
}

/**
 * Generate a unique shareable link ID
 */
export function generateShareId(): string {
  const characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 12; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return result;
}

/**
 * Generate a complete shareable link
 */
export function generateShareableLink(
  permission: SharePermission = 'view',
  expiration: ShareExpiration = '7d'
): ShareLink {
  const id = generateShareId();
  const url = `${typeof window !== 'undefined' ? window.location.origin : 'https://expenses.app'}/share/${id}`;
  const createdAt = new Date();
  const expiresAt = calculateExpirationDate(expiration);

  return {
    id,
    url,
    permission,
    expiration,
    createdAt,
    expiresAt,
    accessCount: 0,
  };
}

/**
 * Calculate expiration date based on duration
 */
function calculateExpirationDate(expiration: ShareExpiration): Date | null {
  if (expiration === 'never') return null;

  const now = new Date();
  switch (expiration) {
    case '24h':
      return new Date(now.getTime() + 24 * 60 * 60 * 1000);
    case '7d':
      return new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    case '30d':
      return new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
  }
}

/**
 * Generate QR code data URL for a share link
 * This is a simplified implementation - in production, you'd use a QR code library
 */
export function generateQRCode(url: string): string {
  // Mock QR code generation - returns a data URL
  // In a real implementation, use a library like 'qrcode' or 'qrcode-react'
  const canvas = typeof document !== 'undefined' ? document.createElement('canvas') : null;

  if (!canvas) {
    // Server-side or no canvas - return placeholder
    return `data:image/svg+xml,${encodeURIComponent(createQRCodeSVG(url))}`;
  }

  // Mock canvas-based QR code
  const ctx = canvas.getContext('2d');
  canvas.width = 200;
  canvas.height = 200;

  if (ctx) {
    // Simple checkerboard pattern as QR code placeholder
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, 200, 200);
    ctx.fillStyle = '#000000';

    // Create a simple pattern
    for (let i = 0; i < 10; i++) {
      for (let j = 0; j < 10; j++) {
        if ((i + j) % 2 === 0) {
          ctx.fillRect(i * 20, j * 20, 20, 20);
        }
      }
    }
  }

  return canvas.toDataURL();
}

/**
 * Create SVG QR code placeholder
 */
function createQRCodeSVG(url: string): string {
  return `
    <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
      <rect width="200" height="200" fill="white"/>
      <rect x="10" y="10" width="30" height="30" fill="black"/>
      <rect x="50" y="10" width="30" height="30" fill="black"/>
      <rect x="90" y="10" width="30" height="30" fill="black"/>
      <rect x="130" y="10" width="30" height="30" fill="black"/>
      <rect x="170" y="10" width="20" height="30" fill="black"/>
      <rect x="10" y="50" width="30" height="30" fill="black"/>
      <rect x="90" y="50" width="30" height="30" fill="black"/>
      <rect x="170" y="50" width="20" height="30" fill="black"/>
      <rect x="10" y="90" width="30" height="30" fill="black"/>
      <rect x="50" y="90" width="30" height="30" fill="black"/>
      <rect x="130" y="90" width="30" height="30" fill="black"/>
      <rect x="170" y="90" width="20" height="30" fill="black"/>
      <rect x="10" y="130" width="30" height="30" fill="black"/>
      <rect x="90" y="130" width="30" height="30" fill="black"/>
      <rect x="170" y="130" width="20" height="30" fill="black"/>
      <rect x="10" y="170" width="30" height="20" fill="black"/>
      <rect x="50" y="170" width="30" height="20" fill="black"/>
      <rect x="90" y="170" width="30" height="20" fill="black"/>
      <rect x="130" y="170" width="30" height="20" fill="black"/>
      <text x="100" y="100" text-anchor="middle" font-size="8" fill="gray">QR Code</text>
    </svg>
  `;
}

/**
 * Copy text to clipboard with fallback
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const successful = document.execCommand('copy');
      textArea.remove();
      return successful;
    }
  } catch (err) {
    console.error('Failed to copy:', err);
    return false;
  }
}

/**
 * Format expiration date for display
 */
export function formatExpirationDate(expiration: ShareExpiration, createdAt: Date): string {
  if (expiration === 'never') return 'Never expires';

  const expiresAt = calculateExpirationDate(expiration);
  if (!expiresAt) return 'Never expires';

  const now = new Date();
  const diff = expiresAt.getTime() - now.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

  if (days > 0) {
    return `Expires in ${days} day${days !== 1 ? 's' : ''}`;
  } else if (hours > 0) {
    return `Expires in ${hours} hour${hours !== 1 ? 's' : ''}`;
  } else {
    return 'Expires soon';
  }
}

/**
 * Get permission description
 */
export function getPermissionDescription(permission: SharePermission): string {
  switch (permission) {
    case 'view':
      return 'Can view expense data';
    case 'download':
      return 'Can view and download';
    case 'full':
      return 'Full access (view, download, re-export)';
  }
}
