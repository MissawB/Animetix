# Design Doc: Task 4 - UI Enhancements (Frontend)

## Goal
Extend `DynamicAuraWrapper` to the `Navbar` (user profile) and `Card` components to make personalization visible across the app.

## Components to Modify

### 1. Navbar (`frontend/src/components/Navbar.tsx`)
- **Change**: Wrap the user profile link with `DynamicAuraWrapper`.
- **Imports**: 
    - Add `DynamicAuraWrapper` import.
    - Fix missing `lucide-react` imports (`Gamepad2`, `Film`, `User`, `Settings`).

### 2. Card (`frontend/src/components/ui/Card.tsx`)
- **Change**: Add an optional `hasAura` prop. If `true`, wrap the card content with `DynamicAuraWrapper`.
- **Props**: Add `hasAura?: boolean` to `CardProps`, defaulting to `false`.

## Implementation Details

### Navbar
```tsx
<DynamicAuraWrapper>
  <Link to={`/profile/${user.username}/`} className="...">
    <User className="..." /> {user.username}
  </Link>
</DynamicAuraWrapper>
```

### Card
```tsx
let content = (
  <div className={`bg-surface-card ...`}>
    {children}
  </div>
);

if (hasAura) {
  content = <DynamicAuraWrapper>{content}</DynamicAuraWrapper>;
}
```

## Testing Strategy
- Verify that the user profile in the Navbar displays the aura if configured in the personalization store.
- Verify that Cards with `hasAura={true}` display the aura.
- Verify that Cards with `hasAura={false}` (default) do not display the aura.
