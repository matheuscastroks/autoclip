import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (name: string) => readFileSync(resolve(__dirname, '../src', name), 'utf8');

describe('desktop interaction stylesheet contract', () => {
  it('loads the desktop foundation after existing styles', () => {
    const main = read('main.ts');
    expect(main.indexOf("'./desktop.css'")).toBeGreaterThan(main.indexOf("'./theme.css'"));
  });
  it('styles both scrollbar axes without replacing native scrolling', () => {
    const css = read('desktop.css');
    expect(css).toContain('::-webkit-scrollbar');
    expect(css).toContain('height: 10px');
    expect(css).toContain('width: 10px');
    expect(css).toContain('.el-scrollbar__thumb');
    expect(read('components/AnalysisPanel.vue')).not.toContain('::-webkit-scrollbar');
    expect(css).toContain('forced-colors: active');
    expect(css).not.toContain('overflow: hidden');
  });
  it('keeps keyboard focus and does not apply global text-selection suppression', () => {
    const css = read('desktop.css');
    expect(css).toContain(':focus-visible');
    expect(css).toContain(':focus:not(:focus-visible)');
    expect(css).not.toMatch(/(?:body|\*)\s*\{[^}]*user-select:\s*none/);
    expect(read('element-theme.css')).not.toMatch(/\.el-button--(?:primary|default):focus\s*\{/);
    expect(read('tokens.css')).toContain("'Segoe UI Variable'");
  });
});
