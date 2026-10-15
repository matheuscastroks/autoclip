import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const css = readFileSync(resolve(__dirname, '../src/tokens.css'), 'utf8');
function color(token: string): string {
  const value = css.match(new RegExp(`--${token}:\\s*(#[\\da-f]{6})`, 'i'))?.[1];
  if (!value) throw new Error(`Missing solid color token: ${token}`);
  return value;
}
function luminance(hex: string) {
  const rgb = hex
    .slice(1)
    .match(/../g)!
    .map(v => parseInt(v, 16) / 255);
  const [r, g, b] = rgb.map(v => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a: string, b: string) {
  const [light, dark] = [luminance(color(a)), luminance(color(b))].sort((x, y) => y - x);
  return (light + 0.05) / (dark + 0.05);
}

describe('readable desktop semantic palette', () => {
  for (const surface of [
    'canvas',
    'surface',
    'surface-raised',
    'surface-hover',
    'surface-selected',
  ]) {
    for (const text of ['primary', 'secondary', 'muted']) {
      it(`${text} text remains readable on ${surface}`, () => {
        expect(contrast(`color-text-${text}`, `color-${surface}`)).toBeGreaterThanOrEqual(4.5);
      });
    }
    it(`keyboard focus remains visible on ${surface}`, () => {
      expect(contrast('color-focus-ring', `color-${surface}`)).toBeGreaterThanOrEqual(3);
    });
  }
  it('keeps primary action text readable in normal and hover states', () => {
    expect(contrast('color-action-primary-text', 'color-action-primary')).toBeGreaterThanOrEqual(
      4.5
    );
    expect(
      contrast('color-action-primary-text', 'color-action-primary-hover')
    ).toBeGreaterThanOrEqual(4.5);
  });
  it('distinguishes editable/control boundaries from their raised surface', () => {
    expect(contrast('color-border-control', 'color-surface-raised')).toBeGreaterThanOrEqual(3);
  });
});
