import { useReaderStore } from './useReaderStore';
import { act } from '@testing-library/react';
import { renderHook } from '@testing-library/react';

test('should switch reader mode', () => {
  const { result } = renderHook(() => useReaderStore());
  act(() => result.current.setMode('webtoon'));
  expect(result.current.mode).toBe('webtoon');
});
