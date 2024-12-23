export class ErrorWithDetails extends Error {
  constructor(message: string, public details: unknown) {
    super(message);
    this.name = 'ErrorWithDetails';
    
    // Maintain proper stack trace
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ErrorWithDetails);
    }
  }
} 