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

  it('does not contain legacy orange accent colors in desktop components', () => {
    const componentsDir = path.resolve(__dirname, '../src/components');
    const vueFiles = fs.readdirSync(componentsDir).filter((file) => file.endsWith('.vue'));
    expect(vueFiles.length).toBeGreaterThan(0);

    const legacyPatterns = [/#d97724/i, /#c4671a/i, /217,\s*119,\s*36/];

    for (const file of vueFiles) {
      const content = fs.readFileSync(path.join(componentsDir, file), 'utf-8');
      for (const pattern of legacyPatterns) {
        expect(
          pattern.test(content),
          `Component ${file} should not contain legacy orange pattern ${pattern}`
        ).toBe(false);
      }
    }
  });

  it('configures ProjectLibrary with list view as default and removes duplicate queue banner', () => {
    const libraryPath = path.resolve(__dirname, '../src/components/ProjectLibrary.vue');
    const libraryContent = fs.readFileSync(libraryPath, 'utf-8');
    expect(libraryContent).toContain("viewMode = ref<'grid' | 'list'>('list')");
    expect(libraryContent).not.toContain('global-queue-banner');
  });

  it('enforces 48px header height token in tokens.css', () => {
    expect(tokensCss).toMatch(/--header-height:\s*48px/);
  });

  it('does not contain keyframes pulse or pulsing animations anywhere in src/', () => {
    const srcDir = path.resolve(__dirname, '../src');
    function scanFiles(dir: string): string[] {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      const files: string[] = [];
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          files.push(...scanFiles(fullPath));
        } else if (/\.(vue|css|ts)$/.test(entry.name)) {
          files.push(fullPath);
        }
      }
      return files;
    }

    const allFiles = scanFiles(srcDir);
    expect(allFiles.length).toBeGreaterThan(0);

    for (const file of allFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      expect(
        content.includes('@keyframes pulse'),
        `File ${path.relative(srcDir, file)} should not define '@keyframes pulse'`
      ).toBe(false);
      expect(
        /animation:\s*pulse\b/.test(content),
        `File ${path.relative(srcDir, file)} should not use 'animation: pulse'`
      ).toBe(false);
    }
  });
});
