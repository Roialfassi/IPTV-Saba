import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock CSS imports
vi.mock('video.js/dist/video-js.css', () => ({}));
