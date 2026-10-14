export interface Interval {
  start: number;
  end: number;
}

export function overlaps(a: Interval, b: Interval): boolean {
  return Math.min(a.end, b.end) > Math.max(a.start, b.start);
}

export function overlapsAny(target: Interval, list: Interval[]): boolean {
  return list.some(item => overlaps(target, item));
}
