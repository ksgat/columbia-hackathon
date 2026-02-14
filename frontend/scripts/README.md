# Prophecy Validation Framework

## 🎯 Purpose

Prevents common errors before they happen:
- ❌ Missing API exports
- ❌ Endpoint mismatches
- ❌ Type inconsistencies
- ❌ Import errors

## 🚀 Usage

### Automatic (runs before dev server)
```bash
npm run dev
# Validation runs automatically!
```

### Manual
```bash
npm run validate
```

## ✅ What It Checks

1. **Required API Exports** (21 functions)
   - Auth: login, logout, getCurrentUser
   - Rooms: createRoom, getRooms, getRoom, joinRoom, getRoomMembers
   - Markets: createMarket, getMarkets, getMarket
   - Trading: placeTrade, previewTrade, getPosition, getTrades
   - Voting: submitVote, getVotes
   - Prophet: generateMarkets, getProphetStatus, getProphetBets

2. **Page Imports**
   - Validates all pages can import required functions
   - Detects missing exports before runtime

3. **Endpoint Consistency**
   - Checks for duplicates
   - Validates paths match backend

## 📊 Output

```
✅ PASSED: 21/21 exports validated
✅ All required API functions exist!
```

or

```
❌ Missing: previewTrade
❌ FAILED: 1 missing exports
```

## 🛠️ How It Prevents Errors

**Before (without validation):**
1. Write code
2. Start dev server
3. Get build error
4. Fix
5. Restart
6. Repeat...

**After (with validation):**
1. Write code
2. Validation catches errors instantly
3. Fix once
4. Dev server starts clean ✨

## 🔧 Extending

Add more checks in `validate-simple.js`:

```javascript
const REQUIRED = [
  // Add your new API function here
  'myNewFunction',
]
```

## 📝 Best Practices

1. **Run validation after adding new API functions**
   ```bash
   npm run validate
   ```

2. **Add validation to CI/CD**
   ```yaml
   - run: npm run validate
   - run: npm run build
   ```

3. **Keep exports list updated**
   - Update `REQUIRED` array when adding features

## 🐛 Troubleshooting

**Validation fails but function exists?**
- Check export format: `export async function name()`
- Not: `function name() {}` (missing export)

**False positives?**
- Check function is actually exported
- Verify spelling matches exactly
