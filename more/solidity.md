# ethereum

[app example](https://github.com/StephenGrider/EthereumCasts)


# smart contracts

[Linux Foundation Hyperledger Fabric](https://www.hyperledger.org/projects/fabric)
[hyperledger composer playground](http://composer-playground.mybluemix.net/login)
[hyperledger composer playground tutorial](https://hyperledger.github.io/composer/latest/tutorials/playground-tutorial.html)
```


# application schema

Business Application -> Hyperledger Composer -> Blockchain ( Hyperledger Fabric)
[documentation](http://solidity.readthedocs.io/en/latest/)


# user app to communicate with Ethereum

* Metamask( chrome extension )
* Mist browser
[Rinkeby ethereum account charger](rinkeby-faucet.com)
[Rinkeby ethereum charger](https://faucet.rinkeby.io)


## account address types

* external ( user account, common for all networks )
* internal ( contract account, specific for each network )
```
balance
storage - data storage
code - compiled machine code 
```

## account credential saving

[bip39](https://iancoleman.io/bip39/)


## [smart contract playground]

(http://remix.ethereum.org)


##SmartContract API collaboration via nodejs app example

* NodeJS ( min version 8.0.1 )
```

# ganache-cli 

const Web3 = require('web3')
const web3 = new Web3("http://localhost:8545")
console.log(web3.eth.getAccounts().then(e=>console.log(e)))
```
* [Java](https://docs.web3j.io/getting_started.html)
* [SpringBoot, gradle example, maven plugin](https://github.com/web3j/)
http://solidity.readthedocs.io/en/latest/


## contract development phases

* create project
```
npm init
npm install -save solc
```
* contract creation ( solidity compiler )
* local testing ( Mocha framework )
```

# npm install mocha ganache-cli web3@1.0.0-beta.26

npm install mocha ganache-cli web3
```
* deployment ( script )
```
truffle
```

# [syntax](http://solidity.readthedocs.io/en/latest/)

[code examples](https://solidity.readthedocs.io/en/latest/solidity-by-example.html)
[references](https://solidity.readthedocs.io/en/latest/solidity-in-depth.html)
[source code of the smart contracts](https://github.com/ethereum/solidity)


## syntax highlighters

* [Atom](https://atom.io/packages/language-ethereum)
```
Open the package installation manager in atom and search for 'language-ethereum'. After installing the package, you might have to manually change the highlighter in the .sol file. Look for the selector at the bottom right of your editor window.
```
[Sublime](https://packagecontrol.io/packages/Ethereum)
[VSCode](https://github.com/juanfranblanco/vscode-solidity)
[Webstorm](https://plugins.jetbrains.com/plugin/9475-intellij-solidity)
[VIM](https://github.com/tomlion/vim-solidity)


## array types

* fixed array
```
uint[5] exampleOfFixedArray;
```
* dynamic array
```
string[] public exampleOfDynamicPublicArray;
```

## function types

* payable
* public/private ( default - public )
* pure ( don't use any contract-variables to manipulate, 'pure' functions  )
* view/constant ( return field, return constant)


## useful functions

* eccak256 
```
built in, which is a version of SHA3. A hash function basically maps an input string into a random 256-bit hexidecimal number.
example:
//b1f078126895a1424524de5321b339ab00408010b7cf0e6ed451514981e58aa9
keccak256("aaaac");
```

