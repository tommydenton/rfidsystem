console.log('Node.js version:', process.version);
console.log('npm version:');
require('child_process').exec('npm -v', (error, stdout) => {
  if (error) {
    console.error('Error executing npm -v:', error);
    return;
  }
  console.log(stdout);
});
