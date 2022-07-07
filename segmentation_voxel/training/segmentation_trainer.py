import torch
from tqdm import tqdm
from vedo import Volume, show

from segmentation_voxel.config.config import Config
from segmentation_voxel.config.mode import DataMode
from segmentation_voxel.data.dataset_nucmm import get_data_loaders
from segmentation_voxel.modeling.voxel_former import SegmentationTransformer3D


class SegmentationTrainer:
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self.data_loaders = get_data_loaders(config)

        num_patches = self.config.model_config.input_shape[1] * self.config.model_config.input_shape[2] * self.config.model_config.input_shape[3] // (self.config.model_config.patch_size ** 3)
        self.model = SegmentationTransformer3D(
            num_classes=self.config.num_classes,
            embed_size=self.config.model_config.embed_size,
            num_heads=self.config.model_config.num_heads,
            input_channels=self.config.model_config.input_channels,
            channels=8,
            patch_size=self.config.model_config.patch_size,
            input_shape=num_patches,
            dropout=self.config.training_config.dropout_probability
        ).to(self.config.device)
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), 
            lr=config.training_config.learning_rate, 
            weight_decay=0.0001, 
            amsgrad=True)
        self.loss = torch.nn.CrossEntropyLoss()
    
    def train(self):
        
        for epoch in range(self.config.training_config.num_epochs):
            self._train_epoch(epoch)
        
    def _train_epoch(self, epoch):
        loader = tqdm(self.data_loaders[DataMode.train])
        for index, data in enumerate(loader):
            self.optimizer.zero_grad()
            image, label = [d.to(self.config.device) for d in data]
            model_output = self.model(image)
            loss = self.loss(model_output, label)
            loss.backward()
            self.optimizer.step()
            loader.set_description(f"Loss: {loss.item():.4f}")
            vol = Volume(model_output[0, 0, :, :, :].detach().cpu().numpy())
        show(vol).close()
    
    def _validate_epoch(self):
        pass
    

if __name__ == "__main__":
    SegmentationTrainer(Config()).train()
