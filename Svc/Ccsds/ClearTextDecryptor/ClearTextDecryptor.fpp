module Svc {
module Ccsds {
    @ WARNING: This component provides NO security. It performs no authentication and
    @ no decryption, passing buffers and contexts through unmodified. It is intended
    @ only for clear-mode operation and testing.
    passive component ClearTextDecryptor {

        import Svc.Ccsds.CcsdsSdlsDecrypt

        @ Warning emitted when traffic is accepted without authentication or decryption
        event NullCipherInUse(securityAssociationIndex: U16) \
            severity warning high \
            format "Null cipher used to decrypt security association {}" \
            throttle 5

        @ Port for requesting the current time
        time get port timeCaller

        @ Port for sending textual representation of events
        text event port logTextOut

        @ Port for sending events to downlink
        event port logOut

    }
}
}
