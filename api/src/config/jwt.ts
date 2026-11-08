import jwt from 'jsonwebtoken';

export interface TokenPayload {
  userId: string;
  email: string;
}

// In production, refuse to start without a real secret instead of silently
// signing tokens with a publicly known default.
if (process.env.NODE_ENV === 'production' && !process.env.JWT_SECRET) {
  throw new Error('JWT_SECRET must be set when NODE_ENV=production');
}

const JWT_SECRET: string = process.env.JWT_SECRET || 'dev_only_jwt_secret_do_not_use_in_production';
const JWT_EXPIRE: string = process.env.JWT_EXPIRE || '7d';

export function generateToken(payload: TokenPayload): string {
  return jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRE } as any);
}

export function verifyToken(token: string): TokenPayload | null {
  try {
    const decoded = jwt.verify(token, JWT_SECRET) as TokenPayload;
    return decoded;
  } catch (error) {
    return null;
  }
}