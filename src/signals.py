"""
Trading signals for the trading bot.
"""

import numpy as np
from config.config import RSI_OVERBOUGHT, RSI_OVERSOLD, PROFIT_TARGET, STOP_LOSS, SYMBOL
from utils.utils import format_price

class SignalGenerator:
    """
    Class for generating trading signals based on technical indicators.
    """
    def __init__(self, market_data):
        """
        Initialize the signal generator.
        
        Args:
            market_data: MarketData instance
        """
        self.market_data = market_data
    
    def analyze_price_trend(self):
        """
        Analyze the price trend based on technical indicators.
        
        Returns:
            tuple: (trend_direction, trend_strength, description)
                trend_direction: "up", "down", or "sideways"
                trend_strength: 0-1 value indicating strength
                description: Text description of the trend
        """
        # Get latest indicators
        indicators = self.market_data.get_latest_indicators()
        if indicators is None:
            return "unknown", 0, "No hay datos suficientes para analizar la tendencia"
        
        # Extract indicator values
        rsi = indicators.get('rsi')
        sma_short = indicators.get('sma_short')
        sma_long = indicators.get('sma_long')
        macd_line = indicators.get('macd_line')
        macd_signal = indicators.get('macd_signal')
        macd_histogram = indicators.get('macd_histogram')
        
        # Get price data
        prices = self.market_data.data['close']
        if len(prices) < 10:
            return "unknown", 0, "No hay datos suficientes para analizar la tendencia"
        
        # Calculate short-term trend (last 5 days)
        short_term_change = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        
        # Calculate medium-term trend (last 20 days)
        medium_term_change = (prices[-1] - prices[-20]) / prices[-20] if len(prices) >= 20 else short_term_change
        
        # Determine trend direction based on multiple factors
        trend_factors = []
        
        # Factor 1: SMA relationship
        if sma_short > sma_long:
            trend_factors.append(("up", 0.7, "SMA corta por encima de SMA larga"))
        elif sma_short < sma_long:
            trend_factors.append(("down", 0.7, "SMA corta por debajo de SMA larga"))
        else:
            trend_factors.append(("sideways", 0.3, "SMAs en equilibrio"))
        
        # Factor 2: MACD
        if macd_histogram > 0 and macd_line > macd_signal:
            trend_factors.append(("up", 0.6, "MACD positivo y creciente"))
        elif macd_histogram < 0 and macd_line < macd_signal:
            trend_factors.append(("down", 0.6, "MACD negativo y decreciente"))
        else:
            trend_factors.append(("sideways", 0.4, "MACD en transición"))
        
        # Factor 3: RSI
        if rsi > 60:
            trend_factors.append(("up", 0.5, f"RSI fuerte ({rsi:.1f})"))
        elif rsi < 40:
            trend_factors.append(("down", 0.5, f"RSI débil ({rsi:.1f})"))
        else:
            trend_factors.append(("sideways", 0.5, f"RSI neutral ({rsi:.1f})"))
        
        # Factor 4: Recent price action
        if short_term_change > 0.02:  # 2% up
            trend_factors.append(("up", 0.8, f"Subida reciente de {short_term_change:.1%}"))
        elif short_term_change < -0.02:  # 2% down
            trend_factors.append(("down", 0.8, f"Caída reciente de {short_term_change:.1%}"))
        else:
            trend_factors.append(("sideways", 0.6, "Precio estable recientemente"))
        
        # Factor 5: Medium-term trend
        if medium_term_change > 0.05:  # 5% up
            trend_factors.append(("up", 0.7, f"Tendencia alcista de {medium_term_change:.1%} en 20 días"))
        elif medium_term_change < -0.05:  # 5% down
            trend_factors.append(("down", 0.7, f"Tendencia bajista de {medium_term_change:.1%} en 20 días"))
        else:
            trend_factors.append(("sideways", 0.5, "Tendencia lateral a medio plazo"))
        
        # Count trend directions
        up_count = sum(1 for direction, _, _ in trend_factors if direction == "up")
        down_count = sum(1 for direction, _, _ in trend_factors if direction == "down")
        sideways_count = sum(1 for direction, _, _ in trend_factors if direction == "sideways")
        
        # Calculate average strength for the dominant trend
        if up_count > down_count and up_count > sideways_count:
            trend_direction = "up"
            trend_strength = sum(strength for direction, strength, _ in trend_factors if direction == "up") / up_count
            trend_reasons = [desc for direction, _, desc in trend_factors if direction == "up"]
            description = f"Tendencia ALCISTA ({trend_strength:.0%}): " + ", ".join(trend_reasons[:2])
        elif down_count > up_count and down_count > sideways_count:
            trend_direction = "down"
            trend_strength = sum(strength for direction, strength, _ in trend_factors if direction == "down") / down_count
            trend_reasons = [desc for direction, _, desc in trend_factors if direction == "down"]
            description = f"Tendencia BAJISTA ({trend_strength:.0%}): " + ", ".join(trend_reasons[:2])
        else:
            trend_direction = "sideways"
            trend_strength = sum(strength for direction, strength, _ in trend_factors if direction == "sideways") / max(sideways_count, 1)
            description = f"Tendencia LATERAL ({trend_strength:.0%}): Mercado sin dirección clara"
        
        return trend_direction, trend_strength, description
    
    def check_buy_signal(self):
        """
        Check if there is a buy signal.
        
        Returns:
            tuple: (is_buy_signal, signal_strength, reason)
        """
        # Get latest indicators
        indicators = self.market_data.get_latest_indicators()
        if indicators is None:
            return False, 0, "No indicator data available"
        
        # Extract indicator values
        rsi = indicators.get('rsi')
        sma_short = indicators.get('sma_short')
        sma_long = indicators.get('sma_long')
        macd_histogram = indicators.get('macd_histogram')
        bb_lower = indicators.get('bb_lower')
        latest_price = self.market_data.get_latest_price()
        
        # Check if any indicators are None
        if None in [rsi, sma_short, sma_long, macd_histogram, bb_lower, latest_price]:
            return False, 0, "Incomplete indicator data"
        
        # Define buy conditions
        conditions = {
            'rsi_oversold': rsi < 40,  # RSI in oversold territory
            'trend_up': sma_short > sma_long,  # Short-term trend is up
            'macd_positive': macd_histogram > 0,  # MACD histogram is positive
            'price_near_bb_lower': latest_price < (bb_lower * 1.05)  # Price near lower Bollinger Band
        }
        
        # Count true conditions
        true_conditions = sum(1 for condition in conditions.values() if condition)
        signal_strength = true_conditions / len(conditions)
        
        # Generate reason text
        reason_parts = []
        for name, condition in conditions.items():
            status = "✅" if condition else "❌"
            if name == 'rsi_oversold':
                reason_parts.append(f"{status} RSI: {rsi:.2f}")
            elif name == 'trend_up':
                reason_parts.append(f"{status} Trend: {'Up' if condition else 'Down'}")
            elif name == 'macd_positive':
                reason_parts.append(f"{status} MACD Histogram: {macd_histogram:.6f}")
            elif name == 'price_near_bb_lower':
                reason_parts.append(f"{status} Price near BB Lower")
        
        reason = ", ".join(reason_parts)
        
        # Determine if this is a buy signal
        is_buy_signal = signal_strength >= 0.75  # At least 75% of conditions are true
        
        return is_buy_signal, signal_strength, reason
    
    def check_sell_signal(self, position):
        """
        Check if there is a sell signal for the current position.
        
        Args:
            position: Position instance
            
        Returns:
            tuple: (is_sell_signal, reason)
        """
        if not position.active:
            return False, "No active position"
        
        # Get latest indicators and price
        indicators = self.market_data.get_latest_indicators()
        if indicators is None:
            return False, "No indicator data available"
        
        latest_price = self.market_data.get_latest_price()
        if latest_price is None:
            return False, "No price data available"
        
        # Calculate profit/loss
        profit_pct = (latest_price - position.entry_price) / position.entry_price
        
        # Extract indicator values
        rsi = indicators.get('rsi')
        macd_histogram = indicators.get('macd_histogram')
        
        # Check take profit
        if profit_pct >= PROFIT_TARGET:
            return True, f"✅ TAKE PROFIT alcanzado: {profit_pct:.2%}"
        
        # Check stop loss
        if profit_pct <= -STOP_LOSS:
            return True, f"🛑 STOP LOSS activado: {profit_pct:.2%}"
        
        # Check technical indicators
        if rsi is not None and macd_histogram is not None:
            if rsi > RSI_OVERBOUGHT and macd_histogram < 0:
                return True, f"📉 Señales técnicas de venta: RSI={rsi:.2f}, MACD Histogram={macd_histogram:.6f}"
        
        # Check time-based exit (if position has been open for more than 7 days and is profitable)
        import datetime
        days_in_position = (datetime.datetime.now() - position.entry_time).days if position.entry_time else 0
        if days_in_position > 7 and profit_pct > 0:
            return True, f"⏱️ Tiempo en posición: {days_in_position} días, Beneficio: {profit_pct:.2%}"
        
        # No sell signal
        return False, f"Mantener posición: {profit_pct:.2%} de P/L"
        
    def forecast_price_range(self):
        """
        Forecast price range for the next hours and days.
        
        Returns:
            dict: Price range forecast with the following keys:
                - short_term: dict with min, max, and likely price for next 24h
                - medium_term: dict with min, max, and likely price for next 3-5 days
                - long_term: dict with min, max, and likely price for next 1-2 weeks
                - confidence: confidence level (0-1)
                - analysis: text description of the forecast
        """
        # Get latest indicators and price data
        indicators = self.market_data.get_latest_indicators()
        if indicators is None:
            return None
        
        # Get current price and historical data
        current_price = self.market_data.get_latest_price()
        prices = self.market_data.data['close']
        
        if current_price is None or len(prices) < 20:
            return None
        
        # Get trend direction and strength
        trend_direction, trend_strength, _ = self.analyze_price_trend()
        
        # Calculate historical volatility (standard deviation of daily returns)
        daily_returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i] - prices[i-1]) / prices[i-1]
            daily_returns.append(daily_return)
        
        if not daily_returns:
            return None
            
        volatility = np.std(daily_returns)
        
        # Get Bollinger Bands for range estimation
        bb_upper_array = indicators.get('bb_upper')
        bb_lower_array = indicators.get('bb_lower')
        
        # Check if arrays exist and have values
        # Handle different types (array or scalar)
        if bb_upper_array is not None:
            if hasattr(bb_upper_array, '__len__'):  # Check if it's an array-like object
                if len(bb_upper_array) > 0:
                    bb_upper = bb_upper_array[-1]  # Get last value
                else:
                    bb_upper = current_price * 1.05  # Empty array fallback
            else:
                bb_upper = bb_upper_array  # It's already a scalar
        else:
            bb_upper = current_price * 1.05  # None fallback
            
        if bb_lower_array is not None:
            if hasattr(bb_lower_array, '__len__'):  # Check if it's an array-like object
                if len(bb_lower_array) > 0:
                    bb_lower = bb_lower_array[-1]  # Get last value
                else:
                    bb_lower = current_price * 0.95  # Empty array fallback
            else:
                bb_lower = bb_lower_array  # It's already a scalar
        else:
            bb_lower = current_price * 0.95  # None fallback
            
        bb_width = (bb_upper - bb_lower) / current_price  # Normalized BB width
        
        # Calculate support and resistance levels
        # Simple method: use recent lows and highs
        recent_prices = prices[-20:]  # Last 20 days
        support_level = min(recent_prices) * 0.99  # Add some margin
        resistance_level = max(recent_prices) * 1.01  # Add some margin
        
        # Calculate price ranges based on volatility and trend
        # Short term (24h) - higher volatility impact
        short_term_factor = volatility * 2  # 2 standard deviations
        
        # Medium term (3-5 days) - trend has more impact
        medium_term_factor = volatility * 3.5  # 3.5 standard deviations
        
        # Long term (1-2 weeks) - trend dominates
        long_term_factor = volatility * 5  # 5 standard deviations
        
        # Adjust based on trend direction and strength
        trend_multiplier = 0
        if trend_direction == "up":
            trend_multiplier = trend_strength
        elif trend_direction == "down":
            trend_multiplier = -trend_strength
        
        # Calculate ranges
        short_term = {
            'min': max(current_price * (1 - short_term_factor), support_level),
            'max': min(current_price * (1 + short_term_factor), resistance_level),
            'likely': current_price * (1 + short_term_factor * trend_multiplier * 0.5)
        }
        
        medium_term = {
            'min': max(current_price * (1 - medium_term_factor), support_level * 0.95),
            'max': min(current_price * (1 + medium_term_factor), resistance_level * 1.05),
            'likely': current_price * (1 + medium_term_factor * trend_multiplier * 0.7)
        }
        
        long_term = {
            'min': max(current_price * (1 - long_term_factor), support_level * 0.9),
            'max': min(current_price * (1 + long_term_factor), resistance_level * 1.1),
            'likely': current_price * (1 + long_term_factor * trend_multiplier)
        }
        
        # Calculate confidence based on volatility and trend strength
        # Lower volatility and stronger trend = higher confidence
        confidence = max(0.3, min(0.9, (1 - volatility * 10) * (0.5 + trend_strength * 0.5)))
        
        # Generate analysis text
        if trend_direction == "up":
            direction_text = "alcista"
            emoji = "📈"
        elif trend_direction == "down":
            direction_text = "bajista"
            emoji = "📉"
        else:
            direction_text = "lateral"
            emoji = "📊"
        
        # Format volatility as percentage
        volatility_pct = volatility * 100
        
        # Calculate expected price changes
        short_term_change = (short_term['likely'] - current_price) / current_price * 100
        medium_term_change = (medium_term['likely'] - current_price) / current_price * 100
        long_term_change = (long_term['likely'] - current_price) / current_price * 100
        
        # Thresholds for significant price movements
        significant_drop_threshold = -3.0  # 3% drop threshold
        significant_rise_threshold = 3.0   # 3% rise threshold
        
        # Initialize variables for price movement detection
        expected_drop = False
        drop_horizon = None
        drop_pct = 0
        
        expected_rise = False
        rise_horizon = None
        rise_pct = 0
        
        # Check for significant drop
        if short_term_change < significant_drop_threshold:
            expected_drop = True
            drop_horizon = "corto plazo (24h)"
            drop_pct = short_term_change
        elif medium_term_change < significant_drop_threshold:
            expected_drop = True
            drop_horizon = "medio plazo (3-5 días)"
            drop_pct = medium_term_change
        elif long_term_change < significant_drop_threshold:
            expected_drop = True
            drop_horizon = "largo plazo (1-2 semanas)"
            drop_pct = long_term_change
            
        # Check for significant rise
        if short_term_change > significant_rise_threshold:
            expected_rise = True
            rise_horizon = "corto plazo (24h)"
            rise_pct = short_term_change
        elif medium_term_change > significant_rise_threshold:
            expected_rise = True
            rise_horizon = "medio plazo (3-5 días)"
            rise_pct = medium_term_change
        elif long_term_change > significant_rise_threshold:
            expected_rise = True
            rise_horizon = "largo plazo (1-2 semanas)"
            rise_pct = long_term_change
        
        analysis = (
            f"{emoji} Con una tendencia {direction_text} (fuerza: {trend_strength:.0%}) "
            f"y volatilidad de {volatility_pct:.1f}%, "
            f"se espera que {SYMBOL} se mueva dentro de los siguientes rangos:\n\n"
            f"*Precio actual:* {format_price(current_price)}\n\n"
            f"• Corto plazo (24h): {format_price(short_term['min'])} - {format_price(short_term['max'])}\n"
            f"• Medio plazo (3-5 días): {format_price(medium_term['min'])} - {format_price(medium_term['max'])}\n"
            f"• Largo plazo (1-2 semanas): {format_price(long_term['min'])} - {format_price(long_term['max'])}\n\n"
            f"*Precio más probable en 24h:* {format_price(short_term['likely'])} "
            f"({short_term_change:.2f}% vs actual)\n\n"
            f"*Niveles clave:*\n"
            f"• Soporte: {format_price(support_level)} ({((support_level - current_price) / current_price * 100):.2f}%)\n"
            f"• Resistencia: {format_price(resistance_level)} ({((resistance_level - current_price) / current_price * 100):.2f}%)"
        )
        
        # Add warnings for expected price movements
        if expected_drop:
            analysis += f"\n\n⚠️ *ALERTA DE BAJADA:* Se espera una caída de {drop_pct:.2f}% en {drop_horizon}."
        
        if expected_rise:
            analysis += f"\n\n🚀 *ALERTA DE SUBIDA:* Se espera un aumento de {rise_pct:.2f}% en {rise_horizon}."
        
        return {
            'short_term': short_term,
            'medium_term': medium_term,
            'long_term': long_term,
            'confidence': confidence,
            'analysis': analysis,
            'support': support_level,
            'resistance': resistance_level,
            'expected_drop': expected_drop,
            'drop_horizon': drop_horizon if expected_drop else None,
            'drop_pct': drop_pct if expected_drop else 0,
            'expected_rise': expected_rise,
            'rise_horizon': rise_horizon if expected_rise else None,
            'rise_pct': rise_pct if expected_rise else 0
        }
