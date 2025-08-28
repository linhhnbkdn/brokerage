"""
Django management command to run the exchange simulator
"""

import asyncio
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

from exchange.services.exchange_simulator import ExchangeSimulator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the exchange simulator to generate dummy market data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=0,
            help='Duration to run simulator (seconds). 0 = run indefinitely'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=2,
            help='Price update interval in seconds'
        )

    def handle(self, *args, **options):
        duration = options['duration']
        interval = options['interval']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting exchange simulator...')
        )
        self.stdout.write(f'Update interval: {interval} seconds')
        if duration > 0:
            self.stdout.write(f'Will run for: {duration} seconds')
        else:
            self.stdout.write('Running indefinitely (Press Ctrl+C to stop)')

        try:
            # Update settings if interval provided
            if interval != 2:
                settings.EXCHANGE_SETTINGS['PRICE_UPDATE_INTERVAL'] = interval
            
            # Run simulator
            simulator = ExchangeSimulator()
            
            # Show initial status
            status = simulator.get_simulation_status()
            self.stdout.write(f"Symbols: {status['symbols_count']}")
            self.stdout.write(f"Supported symbols: {', '.join(status['supported_symbols'][:10])}...")
            
            if duration > 0:
                # Run for specified duration
                asyncio.run(self._run_with_timeout(simulator, duration))
            else:
                # Run indefinitely
                asyncio.run(simulator.start_simulation())
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nSimulator stopped by user')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Simulator error: {str(e)}')
            )

    async def _run_with_timeout(self, simulator, duration):
        """Run simulator for specified duration"""
        try:
            # Start simulator in background
            task = asyncio.create_task(simulator.start_simulation())
            
            # Wait for duration
            await asyncio.sleep(duration)
            
            # Stop simulator
            await simulator.stop_simulation()
            
            # Cancel the task
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
                
        except Exception as e:
            logger.error(f"Error in timed simulation: {str(e)}")
            raise