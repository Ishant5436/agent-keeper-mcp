// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title X402Receipt
/// @notice Non-custodial receipt registry for x402 payment permits.
/// @dev Records that `payer` signed an EIP-712 permit naming `payee` and
///      `amount`. It does NOT move funds: no payable functions, no token
///      calls, no owner, no admin, no upgrade path. `amount` is an opaque
///      uint256 the payer attests to (the off-chain convention is USDC base
///      units, 6 decimals). Signatures are checked with ecrecover, so only
///      EOA payers are supported (no EIP-1271). Anyone may submit a signed
///      permit; the signature, not msg.sender, authorises it.
contract X402Receipt {
    string public constant NAME = "KeeperHub x402 Gateway";
    string public constant VERSION = "1";

    bytes32 private constant DOMAIN_TYPEHASH =
        keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)");
    bytes32 private constant PERMIT_TYPEHASH =
        keccak256("Permit(address payer,address payee,uint256 amount,uint256 nonce,uint256 deadline)");

    /// @dev secp256k1n / 2. Signatures with s above this are malleable twins.
    uint256 private constant HALF_N = 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0;

    /// @notice payer => nonce => already settled.
    mapping(address => mapping(uint256 => bool)) public used;

    event Settled(address indexed payer, address indexed payee, uint256 amount, uint256 nonce);

    error Expired();
    error NonceUsed();
    error BadSignature();

    /// @notice EIP-712 domain separator; computed per call so it tracks block.chainid.
    function domainSeparator() public view returns (bytes32) {
        return keccak256(
            abi.encode(
                DOMAIN_TYPEHASH, keccak256(bytes(NAME)), keccak256(bytes(VERSION)), block.chainid, address(this)
            )
        );
    }

    /// @notice Verify `signature` by `payer` over the permit and record the receipt.
    function settle(
        address payer,
        address payee,
        uint256 amount,
        uint256 nonce,
        uint256 deadline,
        bytes calldata signature
    ) external {
        if (block.timestamp > deadline) revert Expired();
        if (used[payer][nonce]) revert NonceUsed();
        if (signature.length != 65 || payer == address(0)) revert BadSignature();

        bytes32 structHash = keccak256(abi.encode(PERMIT_TYPEHASH, payer, payee, amount, nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", domainSeparator(), structHash));

        bytes32 r = bytes32(signature[0:32]);
        bytes32 s = bytes32(signature[32:64]);
        uint8 v = uint8(signature[64]);
        if (uint256(s) > HALF_N || (v != 27 && v != 28)) revert BadSignature();
        if (ecrecover(digest, v, r, s) != payer) revert BadSignature();

        used[payer][nonce] = true;
        emit Settled(payer, payee, amount, nonce);
    }
}
