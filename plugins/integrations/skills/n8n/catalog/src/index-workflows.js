#!/usr/bin/env node

const { program } = require('commander');
const WorkflowDatabase = require('./database');

function printBanner() {
  console.log('📚 N8N Workflow Indexer');
  console.log('=' .repeat(30));
}

async function indexWorkflows(force = false) {
  const db = new WorkflowDatabase();
  
  try {
    console.log('🔄 Starting workflow indexing...');
    await db.initialize();
    
    const results = await db.indexWorkflows(force);
    
    console.log('✅ Indexing completed!');
    console.log(`📊 Results:`);
    console.log(`   • Processed: ${results.processed}`);
    console.log(`   • Skipped: ${results.skipped}`);
    console.log(`   • Errors: ${results.errors}`);
    console.log(`   • Total files: ${results.total}`);
    
    // Show final stats
    const stats = await db.getStats();
    console.log(`\n📈 Database Statistics:`);
    console.log(`   • Total workflows: ${stats.total}`);
    console.log(`   • Active workflows: ${stats.active}`);
    console.log(`   • Unique integrations: ${stats.unique_integrations}`);
    console.log(`   • Total nodes: ${stats.total_nodes}`);
    
  } catch (error) {
    console.error('❌ Indexing failed:', error.message);
    process.exit(1);
  } finally {
    db.close();
  }
}

// CLI interface
program
  .description('Index N8N workflows into the database')
  .option('-f, --force', 'Force reindexing of all workflows')
  .option('--stats', 'Show database statistics only')
  .parse();

const options = program.opts();

async function main() {
  printBanner();
  
  const db = new WorkflowDatabase();
  
  if (options.stats) {
    try {
      await db.initialize();
      const stats = await db.getStats();
      console.log('📊 Database Statistics:');
      console.log(`   • Total workflows: ${stats.total}`);
      console.log(`   • Active workflows: ${stats.active}`);
      console.log(`   • Inactive workflows: ${stats.inactive}`);
      console.log(`   • Unique integrations: ${stats.unique_integrations}`);
      console.log(`   • Total nodes: ${stats.total_nodes}`);
      console.log(`   • Last indexed: ${stats.last_indexed}`);
      
      if (stats.triggers) {
        console.log(`   • Trigger types:`);
        Object.entries(stats.triggers).forEach(([type, count]) => {
          console.log(`     - ${type}: ${count}`);
        });
      }
      
      if (stats.complexity) {
        console.log(`   • Complexity distribution:`);
        Object.entries(stats.complexity).forEach(([level, count]) => {
          console.log(`     - ${level}: ${count}`);
        });
      }
    } catch (error) {
      console.error('❌ Error fetching stats:', error.message);
      process.exit(1);
    } finally {
      db.close();
    }
  } else {
    await indexWorkflows(options.force);
  }
}

if (require.main === module) {
  main();
}

module.exports = { indexWorkflows }; 