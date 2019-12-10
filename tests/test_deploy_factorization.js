const compose = require('docker-compose');
const path = require('path');

async function run(test_name) {
    const options = {cwd: path.join("/home/avishai/CLionProjects/docker-environment/"), log: true};
    await compose.upAll(options)
        .then(
            async () => {
                console.log('up succeeded')
            },
            err => {
                console.log('something went wrong:', err.message)
            }
        );
    let command_arg = 'sleep 30s; yarn test:integration test/integrationTests/' + test_name;
    await compose.exec('client', ['/bin/bash', '-c', command_arg] , options).then(
        () => {
            console.log('test succeeded')
        },
        err => {
            console.log('something went wrong:', err.message)
        }
    );
    await compose.down(options)
        .then(
            () => {
                console.log('done')
            },
            err => {
                console.log('something went wrong:', err.message)
            }
        );
}

// deployment
run('02_deploy_factorization.spec.js');
