# Frontend Angular Web App Guidelines (Scope Override: /src)

## Architectural & Design Guidelines
- **Framework**: Angular 20 + TypeScript strict mode + RxJS signals.
- **Design System**: Classic Telescopic Text typography (`Georgia` 36px/48px serif canvas, `max-width: 640px` centered layout, pure `#ffffff` background).
- **Triggers & Interactions**: Render clickable triggers as grey pills (`#ebebeb` background, hover `#dcdcdc`, rounded). Double-clicking expanded text containers collapses them back to their original trigger word.
- **Header & Navigation**: Top muted navigation bar (`TelescopicText.org`, `Settings` toggle drawer, `Reset` link).
- **Settings Drawer**: Slid-in `#settings-panel` with dynamic LLM provider model cards, status badges, and in-memory BYOK key input.
- **State Management**: Utilize Angular `signal<T>` signals for component state (`prompt`, `story`, `modelsList`, `selectedModelId`, `userApiKeys`, `isSettingsOpen`).
- **Component Isolation**: Keep components focused, modular, and reusable (`app-root`, `app-story-node`).

## Quality & Testing
- **Run Unit Tests**: `npm test` or `ng test`
- **Build Verification**: `npm run build` (`ng build`)
- Ensure all component specs unit test signal states, user interactions, and service error handling.

