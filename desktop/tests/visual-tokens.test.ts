import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('visual tokens integrity', () => {
  const tokensPath = path.resolve(__dirname, '../src/tokens.css');
  const elementThemePath = path.resolve(__dirname, '../src/element-theme.css');

  const tokensCss = fs.readFileSync(tokensPath, 'utf-8');
  const elementThemeCss = fs.readFileSync(elementThemePath, 'utf-8');

  it('defines neutral studio foundation tokens in tokens.css', () => {
    expect(tokensCss).toMatch(/--color-canvas:\s*#0d0f11/);
    expect(tokensCss).toMatch(/--color-surface:\s*#16181b/);
    expect(tokensCss).toMatch(/--color-surface-selected:\s*#292d32/);
    expect(tokensCss).toMatch(/--color-action-primary:\s*#e5e7eb/);
  });

  it('does not contain legacy orange accent colors in tokens.css or element-theme.css', () => {
    const legacyColors = ['#d97724', '#c4671a', '217, 119, 36'];

    for (const legacy of legacyColors) {
      expect(tokensCss, `tokens.css should not contain legacy color '${legacy}'`).not.toContain(legacy);
      expect(elementThemeCss, `element-theme.css should not contain legacy color '${legacy}'`).not.toContain(legacy);
    }
  });
});
