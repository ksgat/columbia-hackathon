#!/usr/bin/env node

/**
 * Simple API Validation - No dependencies needed
 * Run: node scripts/validate-simple.js
 */

const fs = require('fs')
const path = require('path')

console.log('🔍 Prophecy API Validation Framework\n')

// Required exports
const REQUIRED = [
  'login', 'logout', 'getCurrentUser',
  'createRoom', 'getRooms', 'getRoom', 'joinRoom', 'getRoomMembers',
  'createMarket', 'getMarkets', 'getMarket',
  'placeTrade', 'previewTrade', 'getPosition', 'getTrades',
  'submitVote', 'getVotes',
  'generateMarkets', 'generateMarketsWithProphet', 'getProphetStatus', 'getProphetBets'
]

// Check exports
console.log('📋 Checking required exports...\n')
const apiFile = fs.readFileSync(path.join(__dirname, '../lib/api.ts'), 'utf-8')

let errors = 0
let passed = 0

for (const name of REQUIRED) {
  const exportPattern = new RegExp(`export (?:async )?(?:function|const) ${name}`)
  if (exportPattern.test(apiFile)) {
    console.log(`✅ ${name}`)
    passed++
  } else {
    console.log(`❌ Missing: ${name}`)
    errors++
  }
}

// Check pages for imports
console.log('\n📄 Checking page imports...\n')

const pages = [
  'app/page.tsx',
  'app/room/[id]/page.tsx',
  'app/room/[id]/market/[marketId]/page.tsx'
]

for (const page of pages) {
  const fullPath = path.join(__dirname, '..', page)
  if (fs.existsSync(fullPath)) {
    const content = fs.readFileSync(fullPath, 'utf-8')

    // Extract imports from api
    const importMatch = content.match(/import\s+{([^}]+)}\s+from\s+['"]@\/lib\/api['"]/)
    if (importMatch) {
      const imports = importMatch[1].split(',').map(s => s.trim())
      const missing = imports.filter(imp => !REQUIRED.includes(imp) && !apiFile.includes(`export const ${imp}`))

      if (missing.length > 0) {
        console.log(`⚠️  ${page}: uses ${imports.length} imports`)
      } else {
        console.log(`✅ ${page}`)
      }
    } else if (content.includes("* as api from '@/lib/api'")) {
      console.log(`✅ ${page} (wildcard import)`)
    }
  }
}

// Summary
console.log('\n' + '='.repeat(50))
if (errors === 0) {
  console.log(`✅ PASSED: ${passed}/${REQUIRED.length} exports validated`)
  console.log('✅ All required API functions exist!')
  process.exit(0)
} else {
  console.log(`❌ FAILED: ${errors} missing exports`)
  console.log(`   ${passed}/${REQUIRED.length} passed`)
  process.exit(1)
}
