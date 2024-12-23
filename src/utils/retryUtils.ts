export async function withRetry<T>(
  operation: () => Promise<T>,
  retries = 3,
  delay = 1000,
  backoff = 2
): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    if (retries > 0) {
      console.warn(`Operation failed, retrying in ${delay}ms... (${retries} retries left)`);
      await new Promise(resolve => setTimeout(resolve, delay));
      return withRetry(operation, retries - 1, delay * backoff, backoff);
    }
    throw error;
  }
}

export async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number = 5000,
  context: string = 'Operation'
): Promise<T> {
  const timeoutPromise = new Promise<T>((_, reject) => {
    setTimeout(() => reject(new Error(`${context} timed out after ${timeoutMs}ms`)), timeoutMs);
  });
  return Promise.race([promise, timeoutPromise]);
} 