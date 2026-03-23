import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  Alert,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import Colors from '../../../constants/Colors';
import Spacing from '../../../constants/Spacing';
import Typography from '../../../constants/Typography';
import api from '../../../utils/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const ITEM_SIZE = (SCREEN_WIDTH - Spacing.screenPadding * 2 - Spacing.sm * 2) / 3;

interface GalleryItem {
  id: string;
  image: string;
  description?: string;
  created_at: string;
}

export default function ClientPhotosScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  
  const [client, setClient] = useState<any>(null);
  const [photos, setPhotos] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [clientRes, galleryRes] = await Promise.all([
        api.get(`/clients/${id}`),
        api.get(`/gallery?client_id=${id}`),
      ]);
      setClient(clientRes.data);
      setPhotos(galleryRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const pickAndUploadImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      base64: true,
      quality: 0.7,
    });

    if (!result.canceled && result.assets[0].base64) {
      setUploading(true);
      try {
        await api.post('/gallery', {
          client_id: id,
          image: `data:image/jpeg;base64,${result.assets[0].base64}`,
          description: `Photo for ${client?.name}`,
        });
        loadData();
      } catch (error: any) {
        Alert.alert('Error', error.response?.data?.detail || 'Failed to upload photo');
      } finally {
        setUploading(false);
      }
    }
  };

  const handleDelete = (photo: GalleryItem) => {
    Alert.alert(
      'Delete Photo',
      'Are you sure you want to delete this photo?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/gallery/${photo.id}`);
              loadData();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete photo');
            }
          },
        },
      ]
    );
  };

  const renderPhoto = ({ item }: { item: GalleryItem }) => (
    <TouchableOpacity
      style={styles.photoItem}
      onLongPress={() => handleDelete(item)}
    >
      <Image
        source={{ uri: item.image.startsWith('data:') ? item.image : `data:image/jpeg;base64,${item.image}` }}
        style={styles.photoImage}
        resizeMode="cover"
      />
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.title}>Photos</Text>
          {client && <Text style={styles.subtitle}>{client.name}</Text>}
        </View>
        <TouchableOpacity onPress={pickAndUploadImage} disabled={uploading}>
          {uploading ? (
            <ActivityIndicator size="small" color={Colors.accent} />
          ) : (
            <Ionicons name="add-circle" size={28} color={Colors.accent} />
          )}
        </TouchableOpacity>
      </View>

      <FlatList
        data={photos}
        renderItem={renderPhoto}
        keyExtractor={item => item.id}
        numColumns={3}
        contentContainerStyle={styles.gridContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.accent}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="images-outline" size={64} color={Colors.textSecondary} />
            <Text style={styles.emptyTitle}>No Photos</Text>
            <Text style={styles.emptyText}>Add before & after photos for {client?.name}</Text>
            <TouchableOpacity style={styles.uploadButton} onPress={pickAndUploadImage}>
              <Ionicons name="camera" size={20} color={Colors.buttonText} />
              <Text style={styles.uploadButtonText}>Add Photo</Text>
            </TouchableOpacity>
          </View>
        }
        ListHeaderComponent={
          photos.length > 0 ? (
            <Text style={styles.hint}>Long press to delete a photo</Text>
          ) : null
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerCenter: { alignItems: 'center' },
  title: { fontSize: Typography.h3, fontWeight: Typography.semibold, color: Colors.text },
  subtitle: { fontSize: Typography.caption, color: Colors.textSecondary },
  gridContent: { padding: Spacing.screenPadding },
  photoItem: {
    width: ITEM_SIZE,
    height: ITEM_SIZE,
    margin: Spacing.xs / 2,
    borderRadius: 8,
    overflow: 'hidden',
  },
  photoImage: { width: '100%', height: '100%' },
  hint: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: Spacing.md,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Spacing.xxl * 2,
    gap: Spacing.md,
  },
  emptyTitle: { fontSize: Typography.h3, fontWeight: Typography.semibold, color: Colors.text },
  emptyText: { fontSize: Typography.body, color: Colors.textSecondary, textAlign: 'center' },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderRadius: 24,
    gap: Spacing.xs,
    marginTop: Spacing.md,
  },
  uploadButtonText: { fontSize: Typography.body, fontWeight: Typography.semibold, color: Colors.buttonText },
});
