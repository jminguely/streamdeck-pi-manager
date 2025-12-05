#!/usr/bin/env python3
"""
CLI interface for Stream Deck Pi Manager.
"""
import argparse
import sys
import logging
from streamdeck_pi import __version__
from streamdeck_pi.core.device import StreamDeckManager


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_info(args):
    """Show device information."""
    manager = StreamDeckManager()
    
    if not manager.connect():
        print("Error: No Stream Deck device found")
        return 1
    
    info = manager.get_device_info()
    
    print("Stream Deck Device Information:")
    print(f"  Type: {info['type']}")
    print(f"  Serial: {info['serial']}")
    print(f"  Firmware: {info['firmware']}")
    print(f"  Key Count: {info['key_count']}")
    print(f"  Key Layout: {info['key_layout']}")
    
    manager.disconnect()
    return 0


def cmd_test(args):
    """Test device connection."""
    manager = StreamDeckManager()
    
    print("Testing Stream Deck connection...")
    
    if not manager.connect():
        print("✗ Failed to connect to device")
        return 1
    
    print("✓ Device connected successfully")
    
    # Test setting brightness
    print("Testing brightness control...")
    manager.set_brightness(50)
    print("✓ Brightness control works")
    
    # Test button display
    print("Testing button display...")
    manager.set_button_text(0, "TEST")
    print("✓ Button display works")
    
    # Clear button
    manager.clear_button(0)
    
    manager.disconnect()
    print("\nAll tests passed!")
    return 0


def cmd_clear(args):
    """Clear all buttons."""
    manager = StreamDeckManager()
    
    if not manager.connect():
        print("Error: No Stream Deck device found")
        return 1
    
    print("Clearing all buttons...")
    manager.clear_all_buttons()
    print("Done!")
    
    manager.disconnect()
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Stream Deck Pi Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Info command
    subparsers.add_parser('info', help='Show device information')
    
    # Test command
    subparsers.add_parser('test', help='Test device connection')
    
    # Clear command
    subparsers.add_parser('clear', help='Clear all buttons')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        'info': cmd_info,
        'test': cmd_test,
        'clear': cmd_clear,
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
