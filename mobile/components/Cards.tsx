import React from 'react';
import { StyleSheet, View, Image, TouchableOpacity } from 'react-native';
import { Card, Text, Surface, useTheme } from 'react-native-paper';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { PRODUCT_ICONS, PRIORITY_COLORS } from '../constants/config';
import type { Product, HistoryMovement, Ticket } from '../types';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

// ─── Product Card ─────────────────────────────────────
interface ProductCardProps {
  product: Product;
  onPress: () => void;
  isGrid?: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onPress, isGrid = true }) => {
  const theme = useTheme();
  const emoji = PRODUCT_ICONS[product.category] || PRODUCT_ICONS.Default;

  if (isGrid) {
    return (
      <Card onPress={onPress} style={styles.gridCard} contentStyle={{ flex: 1 }}>
        <Card.Content style={styles.gridContent}>
          <Text style={styles.emojiVisual}>{emoji}</Text>
          <Text style={styles.cardTitle} numberOfLines={1}>{product.name}</Text>
          <Text style={styles.cardRef} numberOfLines={1}>{product.ref}</Text>
          
          <View style={styles.cardFooter}>
            <Text style={styles.cardQty}>Qty: {product.quantity}</Text>
            <View style={[
              styles.statusBadge, 
              product.quantity <= 2 ? styles.statusBadgeLow : styles.statusBadgeOk
            ]}>
              <Text style={[
                styles.statusBadgeText,
                product.quantity <= 2 ? styles.statusBadgeTextLow : styles.statusBadgeTextOk
              ]}>
                {product.quantity <= 2 ? 'Low' : 'Stock'}
              </Text>
            </View>
          </View>
        </Card.Content>
      </Card>
    );
  }

  return (
    <Card onPress={onPress} style={styles.listCard}>
      <Card.Content style={styles.listContent}>
        <Text style={styles.emojiVisualList}>{emoji}</Text>
        <View style={styles.listTextSection}>
          <Text style={styles.cardTitle}>{product.name}</Text>
          <Text style={styles.cardRef}>{product.ref}</Text>
        </View>
        <View style={styles.listRightSection}>
          <Text style={styles.listCardQty}>Qty: {product.quantity}</Text>
          <Text style={styles.listCardPrice}>€{product.price}</Text>
        </View>
      </Card.Content>
    </Card>
  );
};

// ─── History Card ─────────────────────────────────────
interface HistoryCardProps {
  movement: HistoryMovement;
}

export const HistoryCard: React.FC<HistoryCardProps> = ({ movement }) => {
  const isReceive = movement.type === 'Receive';
  return (
    <Card style={styles.historyCard}>
      <Card.Content style={styles.historyContent}>
        <View style={[styles.historyIconBox, { backgroundColor: isReceive ? '#ECFDF5' : '#FEF2F2' }]}>
          <MaterialCommunityIcons 
            name={isReceive ? 'arrow-down-left' : 'arrow-up-right'} 
            size={20} 
            color={isReceive ? Colors.success : Colors.error} 
          />
        </View>
        <View style={styles.historyTextSection}>
          <View style={styles.historyHeader}>
            <Text style={styles.historyTitle}>{movement.productName}</Text>
            <Text style={styles.historyQty}>Qty: {movement.quantity}</Text>
          </View>
          <Text style={styles.historyMeta}>
            by {movement.technician} • {new Date(movement.date).toLocaleDateString()}
          </Text>
          <Text style={styles.historyComment} numberOfLines={2}>
            {movement.comment}
          </Text>
        </View>
      </Card.Content>
    </Card>
  );
};

// ─── Ticket Card ──────────────────────────────────────
interface TicketCardProps {
  ticket: Ticket;
  onPress?: () => void;
  isSelected?: boolean;
}

export const TicketCard: React.FC<TicketCardProps> = ({ ticket, onPress, isSelected = false }) => {
  const priorityColor = PRIORITY_COLORS[ticket.priority] || Colors.textSecondary;
  const theme = useTheme();

  return (
    <Card 
      onPress={onPress} 
      style={[
        styles.ticketCard, 
        isSelected && { borderColor: theme.colors.primary, borderWidth: 1.5 }
      ]}
    >
      <Card.Content>
        <View style={styles.ticketHeader}>
          <Text style={styles.ticketId}>{ticket.id}</Text>
          <View style={[styles.priorityBadge, { backgroundColor: priorityColor + '1A' }]}>
            <Text style={[styles.priorityBadgeText, { color: priorityColor }]}>{ticket.priority}</Text>
          </View>
        </View>
        <Text style={styles.ticketEquipment}>{ticket.requestedEquipment}</Text>
        <Text style={styles.ticketMeta}>
          Requested by {ticket.requester} ({ticket.department})
        </Text>
        <Text style={styles.ticketReason} numberOfLines={2}>"{ticket.reason}"</Text>
      </Card.Content>
    </Card>
  );
};

// ─── Statistic Card ───────────────────────────────────
interface StatisticCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  icon: string;
  iconColor: string;
}

export const StatisticCard: React.FC<StatisticCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  iconColor,
}) => {
  return (
    <Surface style={styles.statCard} elevation={1}>
      <View style={styles.statHeader}>
        <Text style={styles.statTitle}>{title}</Text>
        <MaterialCommunityIcons name={icon} size={20} color={iconColor} />
      </View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statSubtitle}>{subtitle}</Text>
    </Surface>
  );
};

const styles = StyleSheet.create({
  // Grid Product Card
  gridCard: {
    flex: 1,
    margin: 5,
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
  },
  gridContent: {
    padding: Spacing.sm,
    flex: 1,
  },
  emojiVisual: {
    fontSize: 28,
    alignSelf: 'center',
    marginVertical: Spacing.sm,
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Colors.text,
  },
  cardRef: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
    fontFamily: 'monospace',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: Spacing.sm,
  },
  cardQty: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.textSecondary,
  },
  statusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusBadgeOk: {
    backgroundColor: '#ECFDF5',
  },
  statusBadgeLow: {
    backgroundColor: '#FEF2F2',
  },
  statusBadgeText: {
    fontSize: 9,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  statusBadgeTextOk: {
    color: Colors.success,
  },
  statusBadgeTextLow: {
    color: Colors.error,
  },

  // List Product Card
  listCard: {
    marginVertical: 4,
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.md,
  },
  listContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.md,
  },
  emojiVisualList: {
    fontSize: 24,
    marginRight: Spacing.md,
  },
  listTextSection: {
    flex: 1,
  },
  listRightSection: {
    alignItems: 'flex-end',
  },
  listCardQty: {
    fontSize: 11,
    fontWeight: 'bold',
    color: Colors.text,
  },
  listCardPrice: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
  },

  // History Card
  historyCard: {
    marginVertical: 4,
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.md,
  },
  historyContent: {
    flexDirection: 'row',
    padding: Spacing.md,
  },
  historyIconBox: {
    width: 38,
    height: 38,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  historyTextSection: {
    flex: 1,
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  historyTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Colors.text,
  },
  historyQty: {
    fontSize: 11,
    fontWeight: 'bold',
    color: Colors.text,
  },
  historyMeta: {
    fontSize: 9,
    color: Colors.textMuted,
    marginTop: 2,
  },
  historyComment: {
    fontSize: 10,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    marginTop: 6,
    backgroundColor: '#F8FAFC',
    padding: 6,
    borderRadius: 6,
  },

  // Ticket Card
  ticketCard: {
    marginVertical: 4,
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.md,
  },
  ticketHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ticketId: {
    fontSize: 11,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  priorityBadgeText: {
    fontSize: 9,
    fontWeight: 'bold',
  },
  ticketEquipment: {
    fontSize: 13,
    fontWeight: 'bold',
    marginTop: 6,
  },
  ticketMeta: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  ticketReason: {
    fontSize: 10,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    marginTop: 8,
    backgroundColor: '#F8FAFC',
    padding: 6,
    borderRadius: 6,
  },

  // Statistic Card
  statCard: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    flex: 1,
    marginHorizontal: 4,
  },
  statHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statTitle: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: Spacing.sm,
    color: Colors.text,
  },
  statSubtitle: {
    fontSize: 9,
    color: Colors.textMuted,
    marginTop: 2,
  },
});
