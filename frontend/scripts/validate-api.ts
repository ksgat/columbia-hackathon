/**
 * API Validation Framework
 *
 * Prevents missing exports and endpoint mismatches
 * Run: npx tsx scripts/validate-api.ts
 */

import * as api from '../lib/api'
import * as fs from 'fs'
import * as path from 'path'

interface ValidationResult {
  passed: boolean
  errors: string[]
  warnings: string[]
}

const result: ValidationResult = {
  passed: true,
  errors: [],
  warnings: []
}

// Required API functions that must exist
const REQUIRED_EXPORTS = [
  // Auth
  'login',
  'logout',
  'getCurrentUser',

  // Rooms
  'createRoom',
  'getRooms',
  'getRoom',
  'joinRoom',
  'getRoomMembers',

  // Markets
  'createMarket',
  'getMarkets',
  'getMarket',

  // Trading
  'placeTrade',
  'previewTrade',
  'getPosition',
  'getTrades',

  // Voting
  'submitVote',
  'getVotes',

  // Prophet
  'generateMarkets',
  'generateMarketsWithProphet',
  'getProphetStatus',
  'getProphetBets',
]

console.log('🔍 Validating API Exports...\n')

// Check all required exports exist
for (const exportName of REQUIRED_EXPORTS) {
  if (!(exportName in api)) {
    result.passed = false
    result.errors.push(`Missing export: ${exportName}`)
    console.log(`❌ Missing: ${exportName}`)
  } else {
    console.log(`✅ Found: ${exportName}`)
  }
}

// Check for duplicate endpoint paths
console.log('\n🔍 Checking for duplicate endpoints...\n')
const apiFileContent = fs.readFileSync(
  path.join(__dirname, '../lib/api.ts'),
  'utf-8'
)

const endpointPattern = /apiCall\(['"`]([^'"`]+)['"`]/g
const endpoints: string[] = []
let match

while ((match = endpointPattern.exec(apiFileContent)) !== null) {
  endpoints.push(match[1])
}

const duplicates = endpoints.filter(
  (item, index) => endpoints.indexOf(item) !== index
)

if (duplicates.length > 0) {
  result.warnings.push(`Duplicate endpoints found: ${duplicates.join(', ')}`)
  console.log(`⚠️  Duplicates: ${duplicates.join(', ')}`)
} else {
  console.log('✅ No duplicate endpoints')
}

// Validate page imports
console.log('\n🔍 Validating page imports...\n')

const PAGES_TO_CHECK = [
  'app/page.tsx',
  'app/login/page.tsx',
  'app/create/page.tsx',
  'app/room/[id]/page.tsx',
  'app/room/[id]/create-market/page.tsx',
  'app/room/[id]/market/[marketId]/page.tsx',
]

for (const pagePath of PAGES_TO_CHECK) {
  const fullPath = path.join(__dirname, '..', pagePath)

  if (!fs.existsSync(fullPath)) {
    result.warnings.push(`Page not found: ${pagePath}`)
    console.log(`⚠️  Not found: ${pagePath}`)
    continue
  }

  const pageContent = fs.readFileSync(fullPath, 'utf-8')

  // Check for api imports
  const importPattern = /import.*from.*['"]@\/lib\/api['"]/
  if (importPattern.test(pageContent)) {
    // Extract what's being imported
    const importMatch = pageContent.match(/import\s+(?:\*\s+as\s+(\w+)|{([^}]+)})\s+from\s+['"]@\/lib\/api['"]/)

    if (importMatch) {
      if (importMatch[1]) {
        // import * as api
        console.log(`✅ ${pagePath}: imports * as ${importMatch[1]}`)
      } else if (importMatch[2]) {
        // import { ... }
        const imports = importMatch[2].split(',').map(s => s.trim())
        const missing = imports.filter(imp => !(imp in api))

        if (missing.length > 0) {
          result.errors.push(`${pagePath}: imports missing exports: ${missing.join(', ')}`)
          console.log(`❌ ${pagePath}: missing ${missing.join(', ')}`)
        } else {
          console.log(`✅ ${pagePath}: all imports valid`)
        }
      }
    }
  }
}

// Final report
console.log('\n' + '='.repeat(50))
console.log('VALIDATION REPORT')
console.log('='.repeat(50))

if (result.errors.length > 0) {
  console.log('\n❌ ERRORS:')
  result.errors.forEach(err => console.log(`  - ${err}`))
}

if (result.warnings.length > 0) {
  console.log('\n⚠️  WARNINGS:')
  result.warnings.forEach(warn => console.log(`  - ${warn}`))
}

if (result.passed && result.errors.length === 0) {
  console.log('\n✅ ALL VALIDATIONS PASSED!')
  process.exit(0)
} else {
  console.log('\n❌ VALIDATION FAILED!')
  process.exit(1)
}
