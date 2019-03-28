#include "nfc/nfc.h"

//HACK: We also need some of the interals:

#define DEVICE_NAME_LENGTH  256
#define DEVICE_PORT_LENGTH  64
#define MAX_USER_DEFINED_DEVICES 4

struct nfc_user_defined_device {
  char name[DEVICE_NAME_LENGTH];
  nfc_connstring connstring;
  bool optional;
};

/**
 * @struct nfc_context
 * @brief NFC library context
 * Struct which contains internal options, references, pointers, etc. used by library
 */
struct nfc_context {
  bool allow_autoscan;
  bool allow_intrusive_scan;
  uint32_t  log_level;
  struct nfc_user_defined_device user_defined_devices[MAX_USER_DEFINED_DEVICES];
  unsigned int user_defined_device_count;
};


/**
 * @struct nfc_device
 * @brief NFC device information
 */
struct nfc_device {
  const nfc_context *context;
  const struct nfc_driver *driver;
  void *driver_data;
  void *chip_data;

  /** Device name string, including device wrapper firmware */
  char    name[DEVICE_NAME_LENGTH];
  /** Device connection string */
  nfc_connstring connstring;
  /** Is the CRC automaticly added, checked and removed from the frames */
  bool    bCrc;
  /** Does the chip handle parity bits, all parities are handled as data */
  bool    bPar;
  /** Should the chip handle frames encapsulation and chaining */
  bool    bEasyFraming;
  /** Should the chip try forever on select? */
  bool    bInfiniteSelect;
  /** Should the chip switch automatically activate ISO14443-4 when
      selecting tags supporting it? */
  bool    bAutoIso14443_4;
  /** Supported modulation encoded in a byte */
  uint8_t  btSupportByte;
  /** Last reported error */
  int     last_error;
};

#include "freefare.c"
#include "mifare.c"
