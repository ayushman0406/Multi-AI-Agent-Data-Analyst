import { numberTokens } from './answer.js'
const v = (s) => numberTokens(s).map((t) => t.value)
const eq = (a, b, m) => { if (JSON.stringify(a) !== JSON.stringify(b)) { console.log('FAIL', m, a, b); process.exitCode = 1 } }
eq(v('revenue was 12.9k'), [12900], 'k suffix')
eq(v('$1.2 million total'), [1200000], 'million')
eq(v('on 2025-03-15 sales were 37%'), [37], 'date skipped')
eq(v('South 12 [1]'), [12], 'ref skipped')
eq(v('$1,234.5 and -3.5'), [1234.5, -3.5], 'basic')
console.log('done')
