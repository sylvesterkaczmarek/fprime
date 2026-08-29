module Svc {
module Ccsds {
    @ WARNING: This component provides NO security. It performs no authentication and
    @ no encryption, passing buffers and contexts through unmodified. It is intended
    @ only for clear-mode operation and testing.
    passive component ClearTextEncryptor {

        import Svc.Ccsds.CcsdsSdlsEncrypt

        @ Warning emitted when traffic is transmitted without authentication or encryption
        event NullCipherInUse(securityAssociationIndex: U16) \
            severity warning high \
            format "Null cipher used to encrypt security association {}" \
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
