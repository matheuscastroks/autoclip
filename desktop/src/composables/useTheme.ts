import { ref } from 'vue';

export type AppTheme = 'dark' | 'light';

function readTheme(): AppTheme {
  try {
    return localStorage.getItem('autoclip-theme') === 'light' ? 'light' : 'dark';
  } catch {
    return 'dark';
  }
}

export const theme = ref<AppTheme>(readTheme());

export function applyTheme(value: AppTheme) {
  theme.value = value;
  document.documentElement.dataset.theme = value;
  try {
    localStorage.setItem('autoclip-theme', value);
  } catch {
    // Keep the selected theme for this session if storage is unavailable.
  }
}

export function useTheme() {
  function toggleTheme() {
    applyTheme(theme.value === 'dark' ? 'light' : 'dark');
  }

  return { theme, toggleTheme };
}
