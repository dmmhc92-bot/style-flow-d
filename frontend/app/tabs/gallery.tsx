import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Image } from 'expo-image';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';

export default function GalleryScreen() {
  const router = useRouter();
  
  const [gallery, setGallery] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  
  const loadGallery = async () => {
    try {
      const response = await api.get('/gallery');
      setGallery(response.data);
    } catch (error) {
      console.error('Failed to load gallery:', error);
    }
  };
  
  useEffect(() => {
    loadGallery();
  }, []);
  
  const onRefresh = async () => {
    setRefreshing(true);
    await loadGallery();
    setRefreshing(false);
  };
  
  const renderGalleryItem = ({ item }: any) => (
    <View style={styles.galleryItem}>
      <View style={styles.photoContainer}>
        <View style={styles.photoSection}>
          <Text style={styles.photoLabel}>Before</Text>
          {item.before_photo ? (
            <Image source={{ uri: item.before_photo }} style={styles.photo} />
          ) : (
            <View style={styles.photoPlaceholder}>
              <Ionicons name="camera" size={32} color={Colors.textSecondary} />
            </View>
          )}
        </View>
        
        <View style={styles.arrowContainer}>
          <Ionicons name="arrow-forward" size={24} color={Colors.accent} />
        </View>
        
        <View style={styles.photoSection}>
          <Text style={styles.photoLabel}>After</Text>
          {item.after_photo ? (
            <Image source={{ uri: item.after_photo }} style={styles.photo} />
          ) : (
            <View style={styles.photoPlaceholder}>
              <Ionicons name="camera" size={32} color={Colors.textSecondary} />
            </View>
          )}
        </View>
      </View>
      
      {item.notes && (
        <Text style={styles.notes}>{item.notes}</Text>
      )}
      
      <Text style={styles.date}>
        {new Date(item.date_taken).toLocaleDateString()}
      </Text>
    </View>
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Gallery</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => router.push('/tabs/clients')}
        >
          <Ionicons name="add" size={24} color={Colors.textInverse} />
        </TouchableOpacity>
      </View>
      
      <FlatList
        data={gallery}
        renderItem={renderGalleryItem}
        keyExtractor={(item: any) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="images-outline" size={64} color={Colors.textLight} />
            <Text style={styles.emptyText}>No photos yet</Text>
            <Text style={styles.emptySubtext}>Add before & after photos to showcase your work</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
  },
  title: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  list: {
    padding: Spacing.screenPadding,
  },
  galleryItem: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 16,
    padding: Spacing.cardPadding,
    marginBottom: Spacing.md,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  photoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  photoSection: {
    flex: 1,
    alignItems: 'center',
  },
  photoLabel: {
    fontSize: Typography.caption,
    fontWeight: Typography.medium,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  photo: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 12,
  },
  photoPlaceholder: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 12,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  arrowContainer: {
    marginHorizontal: Spacing.sm,
  },
  notes: {
    fontSize: Typography.bodySmall,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  date: {
    fontSize: Typography.caption,
    color: Colors.textLight,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.xxl,
  },
  emptyText: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.textSecondary,
    marginTop: Spacing.md,
  },
  emptySubtext: {
    fontSize: Typography.body,
    color: Colors.textLight,
    marginTop: Spacing.xs,
    textAlign: 'center',
    paddingHorizontal: Spacing.xl,
  },
});