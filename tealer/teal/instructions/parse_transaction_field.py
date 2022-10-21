"""Parser for transaction fields.

Each transaction field is represented as a class. Parsing the field
is creating the class instance representing the field given it's
string representation.

Most of the transaction fields doesn't have immediate arguments
and their string representation consists of single sequence of characters.
Few transaction fields are arrays and have single immediate argument
which is the index into the array. Transaction fields with single immediate
argument are parsed case by case. For other fields, a map(dict) from the
string representation of transaction field to corresponding class is
constructed and are parsed by a simple lookup.

Attributes:
    TX_FIELD_TXT_TO_OBJECT: Map(dict) from string representation
        of transaction field to the corresponding class.
"""

from tealer.teal.instructions import transaction_field

TX_FIELD_TXT_TO_OBJECT = {
    "Sender": transaction_field.Sender,
    "Fee": transaction_field.Fee,
    "FirstValid": transaction_field.FirstValid,
    "FirstValidTime": transaction_field.FirstValidTime,
    "LastValid": transaction_field.LastValid,
    "Note": transaction_field.Note,
    "Lease": transaction_field.Lease,
    "Receiver": transaction_field.Receiver,
    "Amount": transaction_field.Amount,
    "CloseRemainderTo": transaction_field.CloseRemainderTo,
    "VotePK": transaction_field.VotePK,
    "SelectionPK": transaction_field.SelectionPK,
    "VoteFirst": transaction_field.VoteFirst,
    "VoteLast": transaction_field.VoteLast,
    "VoteKeyDilution": transaction_field.VoteKeyDilution,
    "Type": transaction_field.Type,
    "TypeEnum": transaction_field.TypeEnum,
    "XferAsset": transaction_field.XferAsset,
    "AssetAmount": transaction_field.AssetAmount,
    "AssetSender": transaction_field.AssetSender,
    "AssetReceiver": transaction_field.AssetReceiver,
    "AssetCloseTo": transaction_field.AssetCloseTo,
    "GroupIndex": transaction_field.GroupIndex,
    "TxID": transaction_field.TxID,
    "ApplicationID": transaction_field.ApplicationID,
    "OnCompletion": transaction_field.OnCompletion,
    "NumAppArgs": transaction_field.NumAppArgs,
    "NumAccounts": transaction_field.NumAccounts,
    "NumApplications": transaction_field.NumApplications,
    "NumAssets": transaction_field.NumAssets,
    "ApprovalProgram": transaction_field.ApprovalProgram,
    "ClearStateProgram": transaction_field.ClearStateProgram,
    "RekeyTo": transaction_field.RekeyTo,
    "ConfigAsset": transaction_field.ConfigAsset,
    "ConfigAssetTotal": transaction_field.ConfigAssetTotal,
    "ConfigAssetDecimals": transaction_field.ConfigAssetDecimals,
    "ConfigAssetDefaultFrozen": transaction_field.ConfigAssetDefaultFrozen,
    "ConfigAssetUnitName": transaction_field.ConfigAssetUnitName,
    "ConfigAssetName": transaction_field.ConfigAssetName,
    "ConfigAssetURL": transaction_field.ConfigAssetURL,
    "ConfigAssetMetadataHash": transaction_field.ConfigAssetMetadataHash,
    "ConfigAssetManager": transaction_field.ConfigAssetManager,
    "ConfigAssetReserve": transaction_field.ConfigAssetReserve,
    "ConfigAssetFreeze": transaction_field.ConfigAssetFreeze,
    "ConfigAssetClawback": transaction_field.ConfigAssetClawback,
    "FreezeAsset": transaction_field.FreezeAsset,
    "FreezeAssetAccount": transaction_field.FreezeAssetAccount,
    "FreezeAssetFrozen": transaction_field.FreezeAssetFrozen,
    "GlobalNumUint": transaction_field.GlobalNumUint,
    "GlobalNumByteSlice": transaction_field.GlobalNumByteSlice,
    "LocalNumUint": transaction_field.LocalNumUint,
    "LocalNumByteSlice": transaction_field.LocalNumByteSlice,
    "ExtraProgramPages": transaction_field.ExtraProgramPages,
    "Nonparticipation": transaction_field.Nonparticipation,
    "NumLogs": transaction_field.NumLogs,
    "CreatedAssetID": transaction_field.CreatedAssetID,
    "CreatedApplicationID": transaction_field.CreatedApplicationID,
    "LastLog": transaction_field.LastLog,
    "StateProofPK": transaction_field.StateProofPK,
}


def _parse_int(x: str) -> int:
    """Parse teal integers.

    Teal supports three formats to write integers, hex, octal and
    decimal. hexadecimal numbers start with the prefix 0x and octal
    numbers have prefix 0.

    Args:
        x: string representation of the teal integer.

    Returns:
        python integer equal to the value represented by the given
        teal integer.
    """

    if x.startswith("0x"):
        return int(x[2:], 16)
    if x.startswith("0"):
        return int(x, 8)
    return int(x)


def parse_transaction_field(tx_field: str, use_stack: bool) -> transaction_field.TransactionField:
    """Parse transaction fields.

    Args:
        tx_field: string representation of the field.
        use_stack: boolean representing whether the array transaction field
            takes it's index from stack instead of as immediate argument.

    Returns:
        object of class corresponding to the given transaction field.
    """

    if tx_field.startswith("Accounts"):
        return transaction_field.Accounts(
            -1 if use_stack else _parse_int(tx_field[len("Accounts ") :])
        )
    if tx_field.startswith("ApplicationArgs"):
        return transaction_field.ApplicationArgs(
            -1 if use_stack else _parse_int(tx_field[len("ApplicationArgs ") :])
        )
    if tx_field.startswith("Applications"):
        return transaction_field.Applications(
            -1 if use_stack else _parse_int(tx_field[len("Applications ") :])
        )
    if tx_field.startswith("Assets"):
        return transaction_field.Assets(-1 if use_stack else _parse_int(tx_field[len("Assets ") :]))
    if tx_field.startswith("Logs"):
        return transaction_field.Logs(-1 if use_stack else _parse_int(tx_field[len("Logs ") :]))

    tx_field = tx_field.replace(" ", "")
    return TX_FIELD_TXT_TO_OBJECT[tx_field]()
