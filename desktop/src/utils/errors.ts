export function errorMessage(error: unknown, fallback = 'Ocorreu um erro inesperado.'): string {
  if (!error) return fallback;
  if (typeof error === 'string') return error;
  if (error instanceof Error) return error.message;
  if (
    typeof error === 'object' &&
    'message' in error &&
    typeof (error as { message: unknown }).message === 'string'
  ) {
    return (error as { message: string }).message;
  }
  return fallback;
}
