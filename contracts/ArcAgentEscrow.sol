// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title ArcAgentEscrow
/// @notice Non-custodial, deterministic agent-to-agent escrow and micropayment router on Circle Arc.
/// @dev On Arc Mainnet (Chain ID 5042), USDC is the 18-decimal native gas asset.
///      This contract manages conditional payouts, software-to-software agent payments,
///      and emergency timeout refunds while adhering strictly to Holzmann Power of 10 Safety Invariants.
contract ArcAgentEscrow {
    string public constant NAME = "ArcAgentEscrow";
    string public constant VERSION = "1";

    enum EscrowState {
        NONEXISTENT,
        ACTIVE,
        RELEASED,
        REFUNDED
    }

    struct Escrow {
        address payable payer;
        address payable provider;
        uint256 amount;
        uint256 releaseDeadline;
        EscrowState state;
    }

    /// @dev Reentrancy mutex lock (1 = UNLOCKED, 2 = LOCKED)
    uint256 private _status;

    /// @notice taskId => Escrow record
    mapping(bytes32 => Escrow) public escrows;

    event EscrowDeposited(
        bytes32 indexed taskId,
        address indexed payer,
        address indexed provider,
        uint256 amount,
        uint256 releaseDeadline
    );

    event EscrowReleased(bytes32 indexed taskId, address indexed provider, uint256 amount);
    event EscrowRefunded(bytes32 indexed taskId, address indexed payer, uint256 amount);
    event MicropaymentSent(
        address indexed sender,
        address indexed recipient,
        uint256 amount,
        bytes32 indexed metadata
    );

    error ReentrancyGuardReentrantCall();
    error InvalidZeroAddress();
    error InvalidAmount();
    error InvalidTimeout();
    error TaskAlreadyExists();
    error TaskNotFound();
    error InvalidState();
    error Unauthorized();
    error TimeoutNotReached();
    error TransferFailed();

    modifier nonReentrant() {
        if (_status == 2) revert ReentrancyGuardReentrantCall();
        _status = 2;
        _;
        _status = 1;
    }

    constructor() {
        _status = 1;
    }

    /// @notice Deposit native USDC into escrow for an autonomous agent task or API service.
    /// @param taskId Unique identifier for the agent task or x402 challenge.
    /// @param provider Address of the agent or service provider authorized to claim.
    /// @param timeoutSeconds Duration in seconds before the payer can claim an emergency refund.
    function depositEscrow(
        bytes32 taskId,
        address payable provider,
        uint256 timeoutSeconds
    ) external payable nonReentrant {
        if (msg.value == 0) revert InvalidAmount();
        if (provider == address(0) || provider == msg.sender) revert InvalidZeroAddress();
        if (timeoutSeconds < 60 || timeoutSeconds > 30 days) revert InvalidTimeout();
        if (escrows[taskId].state != EscrowState.NONEXISTENT) revert TaskAlreadyExists();

        uint256 deadline = block.timestamp + timeoutSeconds;
        escrows[taskId] = Escrow({
            payer: payable(msg.sender),
            provider: provider,
            amount: msg.value,
            releaseDeadline: deadline,
            state: EscrowState.ACTIVE
        });

        emit EscrowDeposited(taskId, msg.sender, provider, msg.value, deadline);
    }

    /// @notice Release escrowed native USDC to the designated provider.
    /// @dev Only the original payer or the contract owner/delegated agent can release upon verified completion.
    /// @param taskId Unique identifier of the active escrow task.
    function releaseEscrow(bytes32 taskId) external nonReentrant {
        Escrow storage esc = escrows[taskId];
        if (esc.state != EscrowState.ACTIVE) revert InvalidState();
        if (msg.sender != esc.payer) revert Unauthorized();

        uint256 payout = esc.amount;
        address payable recipient = esc.provider;
        esc.state = EscrowState.RELEASED;

        (bool success, ) = recipient.call{value: payout}("");
        if (!success) revert TransferFailed();

        emit EscrowReleased(taskId, recipient, payout);
    }

    /// @notice Emergency refund of escrowed native USDC to the payer after timeout deadline.
    /// @param taskId Unique identifier of the expired escrow task.
    function refundEscrow(bytes32 taskId) external nonReentrant {
        Escrow storage esc = escrows[taskId];
        if (esc.state != EscrowState.ACTIVE) revert InvalidState();
        if (msg.sender != esc.payer) revert Unauthorized();
        if (block.timestamp < esc.releaseDeadline) revert TimeoutNotReached();

        uint256 refundAmount = esc.amount;
        address payable payer = esc.payer;
        esc.state = EscrowState.REFUNDED;

        (bool success, ) = payer.call{value: refundAmount}("");
        if (!success) revert TransferFailed();

        emit EscrowRefunded(taskId, payer, refundAmount);
    }

    /// @notice Direct instant micropayment from one agent to another moving native USDC.
    /// @param recipient Target agent or service provider address.
    /// @param metadata Optional hash of prompt, job ID, or invoice.
    function directMicropayment(
        address payable recipient,
        bytes32 metadata
    ) external payable nonReentrant {
        if (msg.value == 0) revert InvalidAmount();
        if (recipient == address(0)) revert InvalidZeroAddress();

        uint256 amount = msg.value;
        (bool success, ) = recipient.call{value: amount}("");
        if (!success) revert TransferFailed();

        emit MicropaymentSent(msg.sender, recipient, amount, metadata);
    }

    /// @notice Query full details of an escrow task.
    function getEscrow(bytes32 taskId)
        external
        view
        returns (
            address payer,
            address provider,
            uint256 amount,
            uint256 releaseDeadline,
            EscrowState state
        )
    {
        Escrow memory esc = escrows[taskId];
        if (esc.state == EscrowState.NONEXISTENT) revert TaskNotFound();
        return (esc.payer, esc.provider, esc.amount, esc.releaseDeadline, esc.state);
    }
}
