# Frontend Angular Web App Guidelines (Scope Override: /src)

## Architectural Guidelines
- **Framework**: Angular 20 + TypeScript strict mode + RxJS signals + Tailwind CSS.
- **Change Detection Strategy**: Use `ChangeDetectionStrategy.OnPush` across components for maximum performance.
- **State Management**: Utilize Angular `signal<T>` signals for component state (`prompt`, `story`, `isLoading`, `error`).
- **Component Isolation**: Keep components focused, modular, and reusable (`app-root`, `app-story-node`).

## Quality & Testing
- **Run Unit Tests**: `npm test` or `ng test`
- **Build Verification**: `npm run build` (`ng build`)
- Ensure all component specs unit test signal states, user interactions, and service error handling.
