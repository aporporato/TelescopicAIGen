import 'zone.js';
import 'zone.js/testing';
import { vi, expect as vitestExpect } from 'vitest';

(globalThis as any).jasmine = {
  createSpyObj: (name: string, methods: string[]) => {
    const obj: any = {};
    methods.forEach((method) => {
      const fn = vi.fn();
      (fn as any).and = {
        returnValue: (val: any) => fn.mockReturnValue(val),
        rejectWith: (err: any) => fn.mockRejectedValue(err),
      };
      obj[method] = fn;
    });
    return obj;
  },
};

(globalThis as any).spyOn = (obj: any, method: string) => {
  const fn = vi.spyOn(obj, method);
  (fn as any).and = {
    returnValue: (val: any) => fn.mockReturnValue(val),
    rejectWith: (err: any) => fn.mockRejectedValue(err),
  };
  return fn;
};

vitestExpect.extend({
  toBeFalse(received) {
    return {
      pass: received === false,
      message: () => `expected ${received} to be false`,
    };
  },
  toBeTrue(received) {
    return {
      pass: received === true,
      message: () => `expected ${received} to be true`,
    };
  },
});
