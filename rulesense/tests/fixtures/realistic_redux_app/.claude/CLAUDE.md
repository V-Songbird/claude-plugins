# Unified Pricing Portal

Enterprise pricing management tool. Monorepo with `packages/ui` (React) and `packages/api` (Express proxy).

## Hard Rules

1. **NEVER install new packages.** Use only existing dependencies. Confirm with user first if strictly required.
2. **All components must be functional** with hooks. No class components.
3. **All user-facing strings** must use react-intl: `<FormattedMessage id="..." />`.
4. **New state** uses Redux Toolkit slices. **New API data** uses RTK Query via `baseApi.injectEndpoints()`.
5. **Tests must maintain 95% coverage** (branches, functions, lines, statements).
6. **Use typed hooks**: `useAppDispatch()` and `useAppSelector()` from `hooks.ts`.
7. **SCSS only** with BEM naming. Reference variables from `_variables.scss`.
8. **Import order**: external libs, internal packages, local absolute, local relative, styles.

## Commands

```bash
npm run start:dev            # Dev servers
npm run build                # Production build
npm run lint:fix             # Auto-fix lint issues
npm run test                 # Unit tests
npm run test:coverage        # Tests with 95% threshold
```

## Architecture

```
Browser -> React UI (:8080) -> Express API proxy (:3000) -> Backend API
```

- **Auth**: Azure AD MSAL. `getAccessToken()` handles silent refresh. 401 -> reset all state.
- **State**: Redux Toolkit. Root reducer resets on `RESET_STORE_ACTION_TYPE`.
- **Routing**: React Router v5 with lazy-loaded pages.
- **Feature flags**: OpenFeature SDK. Keys in `featureKeys.ts`.

## File Naming

| Type | Convention | Example |
|------|-----------|---------|
| Components | PascalCase `.tsx` | `FeesPage.tsx` |
| Hooks | camelCase `use` prefix | `useAppToast.ts` |
| Redux slices | kebab-case `-slice.ts` | `rate-card-inputs-slice.ts` |
| Tests | Same name + `.test.js` | `FeesPage.test.js` |

## RTK Query Pattern

New API endpoints follow this pattern:

```typescript
import baseApi from './baseApi';

const entityApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getEntities: build.query({
      query: getEntitiesQuery,
      providesTags: ['TagName'],
    }),
  }),
});

export const { useGetEntitiesQuery } = entityApi;
```

**Important**: Add new tag types to `baseApi.ts` tagTypes array first.

## Testing Patterns

### Test Helpers

| Helper | Type | Description |
|--------|------|-------------|
| `shallow(jsx)` | Enzyme | Shallow render |
| `mount(jsx)` | Enzyme | Full DOM render |
| `shallowWithIntl(jsx)` | Custom | Shallow with IntlProvider |
| `dispatch` | jest.fn() | Pre-mocked dispatch |
| `setAppState(state)` | Function | Mocks useAppSelector |

### Standard Test Structure

```javascript
import React from 'react';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  beforeEach(() => {
    setAppState({ feature: { data: [] } });
  });

  it('renders correctly', () => {
    const wrapper = shallowWithIntl(<MyComponent id="123" />);
    expect(wrapper).toMatchSnapshot();
  });
});
```

## API Integration

- Use `axiosBaseQuery` shape: `{ url, method, data, params }`.
- URL is relative. `BASE_PATH` prepended automatically.
- Always handle loading and error states in components.
